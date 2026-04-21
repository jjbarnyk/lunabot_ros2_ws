"""
odometry_node.py
================
Reads encoder feedback from motor controllers over CAN bus and publishes
accurate wheel odometry to /odom and TF odom→base_link.

Each motor controller sends back encoder ticks at ~50 Hz:
  CAN ID 0x201 → Front-Left  encoder
  CAN ID 0x202 → Front-Right encoder
  CAN ID 0x203 → Rear-Left   encoder
  CAN ID 0x204 → Rear-Right  encoder

Encoder frame (8 bytes):
  Byte 0-3: tick count as int32 big-endian (cumulative)
  Byte 4-7: reserved

NOTE: If your motor controllers use a different frame format,
      update _parse_encoder_frame() to match.
"""

import math
import struct

import can
import rclpy
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from tf2_ros import TransformBroadcaster


WHEEL_BASE          = 0.58    # metres — matches URDF
WHEEL_RADIUS        = 0.15    # metres
TICKS_PER_REV       = 4096   # encoder ticks per full wheel revolution — tune to your motors

CAN_INTERFACE       = 'can0'
ENC_ID_FRONT_LEFT   = 0x201
ENC_ID_FRONT_RIGHT  = 0x202
ENC_ID_REAR_LEFT    = 0x203
ENC_ID_REAR_RIGHT   = 0x204

METRES_PER_TICK = (2.0 * math.pi * WHEEL_RADIUS) / TICKS_PER_REV


class OdometryNode(Node):

    def __init__(self):
        super().__init__('odometry_node')

        self.declare_parameter('can_interface', CAN_INTERFACE)
        self.declare_parameter('wheel_base', WHEEL_BASE)
        self.declare_parameter('ticks_per_rev', TICKS_PER_REV)

        self._wheel_base    = self.get_parameter('wheel_base').value
        self._ticks_per_rev = self.get_parameter('ticks_per_rev').value
        self._mpt           = (2.0 * math.pi * WHEEL_RADIUS) / self._ticks_per_rev
        can_iface           = self.get_parameter('can_interface').value

        # ── CAN bus (read-only listener) ─────────────────────────────────────
        try:
            self._bus = can.interface.Bus(channel=can_iface, bustype='socketcan')
            self.get_logger().info(f'Encoder CAN listener on {can_iface}')
        except Exception as e:
            self.get_logger().fatal(f'Cannot open CAN bus: {e}')
            raise SystemExit(1)

        # ── Publishers ───────────────────────────────────────────────────────
        self._odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self._tf_br    = TransformBroadcaster(self)

        # ── Odometry state ───────────────────────────────────────────────────
        self._x     = 0.0
        self._y     = 0.0
        self._theta = 0.0

        # Previous tick counts per wheel
        self._prev_ticks = {
            ENC_ID_FRONT_LEFT:  None,
            ENC_ID_FRONT_RIGHT: None,
            ENC_ID_REAR_LEFT:   None,
            ENC_ID_REAR_RIGHT:  None,
        }

        self._last_time = self.get_clock().now()

        # Poll CAN bus at 50 Hz
        self.create_timer(0.02, self._read_can)

        self.get_logger().info('Odometry node ready — reading encoder CAN frames.')

    def _read_can(self):
        """Non-blocking read of all pending CAN frames."""
        while True:
            msg = self._bus.recv(timeout=0.0)
            if msg is None:
                break
            if msg.arbitration_id in self._prev_ticks:
                self._handle_encoder(msg)

    def _handle_encoder(self, msg: can.Message):
        enc_id = msg.arbitration_id
        ticks  = self._parse_encoder_frame(msg.data)
        if ticks is None:
            return

        prev = self._prev_ticks[enc_id]
        self._prev_ticks[enc_id] = ticks

        if prev is None:
            return  # First reading — no delta yet

        delta_ticks = ticks - prev
        delta_m     = delta_ticks * self._mpt

        # Average left and right deltas when both sides have updated
        # Use front wheels as primary; rear wheels as validation
        if enc_id in (ENC_ID_FRONT_LEFT, ENC_ID_REAR_LEFT):
            self._left_delta  = delta_m
        elif enc_id in (ENC_ID_FRONT_RIGHT, ENC_ID_REAR_RIGHT):
            self._right_delta = delta_m

        # Publish when both sides updated
        if hasattr(self, '_left_delta') and hasattr(self, '_right_delta'):
            self._publish_odom(self._left_delta, self._right_delta)
            del self._left_delta
            del self._right_delta

    def _parse_encoder_frame(self, data: bytes):
        """
        Parse encoder CAN frame.
        Default: int32 big-endian tick count in bytes 0-3.
        Update this to match your motor controller's actual format.
        """
        if len(data) < 4:
            return None
        try:
            (ticks,) = struct.unpack_from('>i', data, 0)
            return ticks
        except struct.error:
            return None

    def _publish_odom(self, left_m: float, right_m: float):
        now = self.get_clock().now()

        # Differential drive integration
        d     = (left_m + right_m) / 2.0
        dtheta = (right_m - left_m) / self._wheel_base

        self._x     += d * math.cos(self._theta + dtheta / 2.0)
        self._y     += d * math.sin(self._theta + dtheta / 2.0)
        self._theta += dtheta

        # ── Odometry message ─────────────────────────────────────────────────
        odom = Odometry()
        odom.header.stamp    = now.to_msg()
        odom.header.frame_id = 'odom'
        odom.child_frame_id  = 'base_link'

        odom.pose.pose.position.x  = self._x
        odom.pose.pose.position.y  = self._y
        odom.pose.pose.orientation.z = math.sin(self._theta / 2.0)
        odom.pose.pose.orientation.w = math.cos(self._theta / 2.0)

        odom.pose.covariance[0]  = 0.02
        odom.pose.covariance[7]  = 0.02
        odom.pose.covariance[35] = 0.05

        self._odom_pub.publish(odom)

        # ── TF odom → base_link ──────────────────────────────────────────────
        tf = TransformStamped()
        tf.header.stamp    = now.to_msg()
        tf.header.frame_id = 'odom'
        tf.child_frame_id  = 'base_link'

        tf.transform.translation.x = self._x
        tf.transform.translation.y = self._y
        tf.transform.translation.z = 0.0
        tf.transform.rotation.z    = math.sin(self._theta / 2.0)
        tf.transform.rotation.w    = math.cos(self._theta / 2.0)

        self._tf_br.sendTransform(tf)

    def destroy_node(self):
        self._bus.shutdown()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = OdometryNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
