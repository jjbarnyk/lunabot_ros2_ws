"""
motor_control_node.py
=====================
ROS 2 Jazzy motor control for Lunabot using REV SPARK MAX controllers.

SPARK MAX CAN Protocol (REV Robotics):
  Each SPARK MAX has a unique Device ID (1-62), set via REV Hardware Client.
  
  CAN Arbitration ID is built from:
    Bits 9-6  : API Class
    Bits 5-0  : Device ID (1-4 for our four motors)
  
  To send a Duty Cycle command (percent output):
    API Class : 0x020 (Motor Control - Duty Cycle)
    Full ID   : (0x020 << 6) | device_id
    Data      : 4 bytes, little-endian float (-1.0 to 1.0)
                -1.0 = full reverse, 0.0 = stop, 1.0 = full forward

Motor Layout:
  Device ID 1 = Front-Left
  Device ID 2 = Front-Right  (spin opposite direction to left)
  Device ID 3 = Rear-Left
  Device ID 4 = Rear-Right   (spin opposite direction to left)

Set these Device IDs in REV Hardware Client before running.
"""

import math
import struct

import can
import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from std_msgs.msg import Bool


# ── Robot geometry (must match lunabot.urdf) ──────────────────────────────────
WHEEL_BASE       = 0.58    # metres — left-to-right track width (from URDF)
WHEEL_RADIUS     = 0.15    # metres — wheel radius (from URDF)
MAX_LINEAR_SPEED = 0.5     # m/s — tune this to your robot's real max speed

# ── CAN interface ─────────────────────────────────────────────────────────────
CAN_INTERFACE = 'can0'

# ── SPARK MAX Device IDs (set these in REV Hardware Client) ───────────────────
ID_FRONT_LEFT  = 1
ID_FRONT_RIGHT = 2
ID_REAR_LEFT   = 3
ID_REAR_RIGHT  = 4

# ── REV SPARK MAX CAN protocol constants ──────────────────────────────────────
# Duty cycle control API class
REV_API_DUTY_CYCLE = 0x020

# Heartbeat — SPARK MAX requires a heartbeat every 100ms or it disables output
# This is a broadcast frame all SPARK MAXes listen to
REV_HEARTBEAT_ID   = 0x2052C80
REV_HEARTBEAT_DATA = bytes([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])

# Safety timeout — stop if no cmd_vel received
CMD_VEL_TIMEOUT = 0.5   # seconds


def spark_max_can_id(device_id: int) -> int:
    """
    Build the CAN arbitration ID for a SPARK MAX duty cycle command.
    Formula: (API_Class << 6) | device_id
    """
    return (REV_API_DUTY_CYCLE << 6) | device_id


def duty_cycle_frame(percent: float) -> bytes:
    """
    Build the 8-byte CAN data frame for a SPARK MAX duty cycle command.
    percent: -1.0 (full reverse) to 1.0 (full forward)
    """
    # Clamp to safe range
    percent = max(-1.0, min(1.0, percent))
    # Pack as little-endian float in first 4 bytes, rest zeros
    return struct.pack('<f4x', percent)


class MotorControlNode(Node):

    def __init__(self):
        super().__init__('motor_control_node')

        # ── Parameters ────────────────────────────────────────────────────────
        self.declare_parameter('can_interface',    CAN_INTERFACE)
        self.declare_parameter('wheel_base',       WHEEL_BASE)
        self.declare_parameter('max_linear_speed', MAX_LINEAR_SPEED)
        self.declare_parameter('id_front_left',    ID_FRONT_LEFT)
        self.declare_parameter('id_front_right',   ID_FRONT_RIGHT)
        self.declare_parameter('id_rear_left',     ID_REAR_LEFT)
        self.declare_parameter('id_rear_right',    ID_REAR_RIGHT)

        self._wheel_base  = self.get_parameter('wheel_base').value
        self._max_speed   = self.get_parameter('max_linear_speed').value
        can_iface         = self.get_parameter('can_interface').value

        self._ids = {
            'fl': self.get_parameter('id_front_left').value,
            'fr': self.get_parameter('id_front_right').value,
            'rl': self.get_parameter('id_rear_left').value,
            'rr': self.get_parameter('id_rear_right').value,
        }

        # ── CAN bus ───────────────────────────────────────────────────────────
        try:
            self._bus = can.interface.Bus(
                channel=can_iface,
                bustype='socketcan'
            )
            self.get_logger().info(f'CAN bus opened on {can_iface}')
        except Exception as e:
            self.get_logger().fatal(f'Cannot open CAN bus: {e}')
            raise SystemExit(1)

        # ── Subscribers ───────────────────────────────────────────────────────
        self.create_subscription(Twist, '/cmd_vel', self._cmd_vel_cb, 10)
        self.create_subscription(Bool,  '/estop',   self._estop_cb,   10)

        # ── Publishers ────────────────────────────────────────────────────────
        self._odom_pub = self.create_publisher(Odometry, '/odom', 10)

        # ── State ─────────────────────────────────────────────────────────────
        self._estopped    = False
        self._last_cmd    = self.get_clock().now()
        self._x           = 0.0
        self._y           = 0.0
        self._theta       = 0.0
        self._last_time   = self.get_clock().now()

        # ── Timers ────────────────────────────────────────────────────────────
        # Heartbeat every 80ms — SPARK MAX needs this or it cuts motor output
        self.create_timer(0.08, self._send_heartbeat)
        # Safety watchdog at 10 Hz
        self.create_timer(0.1,  self._watchdog)

        self.get_logger().info('SPARK MAX motor control node ready.')
        self.get_logger().info(
            f'Device IDs — FL:{self._ids["fl"]} FR:{self._ids["fr"]} '
            f'RL:{self._ids["rl"]} RR:{self._ids["rr"]}'
        )

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _cmd_vel_cb(self, msg: Twist):
        if self._estopped:
            return

        self._last_cmd = self.get_clock().now()

        linear  = msg.linear.x
        angular = msg.angular.z

        # Differential drive kinematics → wheel speeds in m/s
        left_mps  = linear - angular * (self._wheel_base / 2.0)
        right_mps = linear + angular * (self._wheel_base / 2.0)

        # Convert m/s → duty cycle (-1.0 to 1.0)
        left_duty  =  left_mps  / self._max_speed
        right_duty =  right_mps / self._max_speed

        # Right side motors are physically mirrored — negate their direction
        self._send_duty(self._ids['fl'],  left_duty)
        self._send_duty(self._ids['rl'],  left_duty)
        self._send_duty(self._ids['fr'], -right_duty)
        self._send_duty(self._ids['rr'], -right_duty)

        # Update odometry
        self._update_odom(linear, angular)

    def _estop_cb(self, msg: Bool):
        if msg.data:
            self.get_logger().warn('E-STOP activated!')
            self._estopped = True
            self._stop_all()
        else:
            self.get_logger().info('E-STOP cleared.')
            self._estopped = False

    def _watchdog(self):
        """Stop motors if no cmd_vel received within timeout."""
        if self._estopped:
            return
        elapsed = (self.get_clock().now() - self._last_cmd).nanoseconds / 1e9
        if elapsed > CMD_VEL_TIMEOUT:
            self._stop_all()

    def _send_heartbeat(self):
        """
        SPARK MAX requires a periodic heartbeat CAN frame.
        Without it, controllers enter safe state and disable motor output.
        """
        msg = can.Message(
            arbitration_id=REV_HEARTBEAT_ID,
            data=REV_HEARTBEAT_DATA,
            is_extended_id=True
        )
        try:
            self._bus.send(msg)
        except can.CanError as e:
            self.get_logger().warn(f'Heartbeat send failed: {e}')

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _send_duty(self, device_id: int, duty: float):
        """Send duty cycle command to one SPARK MAX."""
        arb_id = spark_max_can_id(device_id)
        data   = duty_cycle_frame(duty)
        msg    = can.Message(
            arbitration_id=arb_id,
            data=data,
            is_extended_id=True    # SPARK MAX uses 29-bit extended CAN IDs
        )
        try:
            self._bus.send(msg)
        except can.CanError as e:
            self.get_logger().error(
                f'CAN send failed [device {device_id}]: {e}')

    def _stop_all(self):
        for dev_id in self._ids.values():
            self._send_duty(dev_id, 0.0)

    def _update_odom(self, linear: float, angular: float):
        now = self.get_clock().now()
        dt  = (now - self._last_time).nanoseconds / 1e9
        self._last_time = now

        self._x     += linear * math.cos(self._theta) * dt
        self._y     += linear * math.sin(self._theta) * dt
        self._theta += angular * dt

        odom = Odometry()
        odom.header.stamp    = now.to_msg()
        odom.header.frame_id = 'odom'
        odom.child_frame_id  = 'base_link'

        odom.pose.pose.position.x  = self._x
        odom.pose.pose.position.y  = self._y
        odom.pose.pose.orientation.z = math.sin(self._theta / 2.0)
        odom.pose.pose.orientation.w = math.cos(self._theta / 2.0)

        odom.twist.twist.linear.x  = linear
        odom.twist.twist.angular.z = angular

        odom.pose.covariance[0]  = 0.1
        odom.pose.covariance[7]  = 0.1
        odom.pose.covariance[35] = 0.2

        self._odom_pub.publish(odom)

    def destroy_node(self):
        self.get_logger().info('Shutting down — stopping all motors.')
        self._stop_all()
        self._bus.shutdown()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = MotorControlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
