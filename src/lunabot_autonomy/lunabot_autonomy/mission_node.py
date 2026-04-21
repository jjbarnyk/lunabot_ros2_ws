"""
mission_node.py
===============
Lunabot mission state machine — navigation only.

Mission sequence:
  1. IDLE          — waiting for operator start
  2. NAVIGATE_OUT  — drive to target zone via Nav2
  3. AT_TARGET     — arrived, dwell briefly, then return
  4. NAVIGATE_HOME — drive back to start
  5. DONE          — mission complete

Topics:
  /mission/start  (std_msgs/Bool)   — publish True to start
  /mission/abort  (std_msgs/Bool)   — publish True to abort
  /mission/state  (std_msgs/String) — current state for dashboard

Set TARGET_ZONE x/y after building your map.
"""

import enum
import math
import time

import rclpy
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node
from std_msgs.msg import Bool, String

# ── Waypoints ─────────────────────────────────────────────────────────────────
# After mapping, echo /odom while at the target spot and paste coords here.
HOME_ZONE   = {'x': 0.0, 'y': 0.0, 'yaw': 0.0}
TARGET_ZONE = {'x': 5.0, 'y': 0.0, 'yaw': 0.0}   # ← SET THIS

# ── Timing ────────────────────────────────────────────────────────────────────
DWELL_AT_TARGET_SEC = 3.0
NAV_TIMEOUT_SEC     = 120.0


class MissionState(enum.Enum):
    IDLE          = 'IDLE'
    NAVIGATE_OUT  = 'NAVIGATE_OUT'
    AT_TARGET     = 'AT_TARGET'
    NAVIGATE_HOME = 'NAVIGATE_HOME'
    DONE          = 'DONE'
    ABORTED       = 'ABORTED'
    NAV_FAILED    = 'NAV_FAILED'


class MissionNode(Node):

    def __init__(self):
        super().__init__('mission_node')

        self._state       = MissionState.IDLE
        self._nav_active  = False
        self._nav_result  = None
        self._nav_start_t = 0.0
        self._dwell_start = 0.0

        self._nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self._state_pub  = self.create_publisher(String, '/mission/state', 10)

        self.create_subscription(Bool, '/mission/start', self._start_cb, 10)
        self.create_subscription(Bool, '/mission/abort', self._abort_cb, 10)
        self.create_timer(0.1, self._mission_loop)

        self.get_logger().info('Mission node ready. Publish True to /mission/start.')

    def _start_cb(self, msg: Bool):
        if msg.data and self._state == MissionState.IDLE:
            self.get_logger().info('START received — navigating to target.')
            self._transition(MissionState.NAVIGATE_OUT)

    def _abort_cb(self, msg: Bool):
        if msg.data:
            self.get_logger().warn('ABORT received.')
            self._cancel_nav()
            self._transition(MissionState.ABORTED)

    def _mission_loop(self):
        self._state_pub.publish(String(data=self._state.value))

        if self._state == MissionState.IDLE:
            pass

        elif self._state == MissionState.NAVIGATE_OUT:
            if not self._nav_active:
                self._navigate_to(TARGET_ZONE)
            elif self._nav_succeeded():
                self.get_logger().info('At target. Dwelling...')
                self._dwell_start = time.time()
                self._transition(MissionState.AT_TARGET)
            elif self._nav_failed():
                self._transition(MissionState.NAV_FAILED)

        elif self._state == MissionState.AT_TARGET:
            if time.time() - self._dwell_start >= DWELL_AT_TARGET_SEC:
                self.get_logger().info('Returning home.')
                self._transition(MissionState.NAVIGATE_HOME)

        elif self._state == MissionState.NAVIGATE_HOME:
            if not self._nav_active:
                self._navigate_to(HOME_ZONE)
            elif self._nav_succeeded():
                self.get_logger().info('Home. Mission DONE.')
                self._transition(MissionState.DONE)
            elif self._nav_failed():
                self._transition(MissionState.NAV_FAILED)

        elif self._state in (MissionState.DONE,
                             MissionState.ABORTED,
                             MissionState.NAV_FAILED):
            pass

    def _navigate_to(self, wp: dict):
        if not self._nav_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error('Nav2 not available!')
            self._transition(MissionState.NAV_FAILED)
            return
        goal = NavigateToPose.Goal()
        goal.pose = self._make_pose(wp)
        self._nav_result  = None
        self._nav_active  = True
        self._nav_start_t = time.time()
        self._nav_client.send_goal_async(goal).add_done_callback(
            self._goal_response_cb)

    def _goal_response_cb(self, future):
        handle = future.result()
        if not handle.accepted:
            self._nav_active = False
            self._nav_result = 'FAILED'
            return
        handle.get_result_async().add_done_callback(self._goal_result_cb)

    def _goal_result_cb(self, future):
        status = future.result().status
        self._nav_active = False
        self._nav_result = ('SUCCEEDED'
                            if status == GoalStatus.STATUS_SUCCEEDED
                            else 'FAILED')

    def _nav_succeeded(self):
        return not self._nav_active and self._nav_result == 'SUCCEEDED'

    def _nav_failed(self):
        timed_out = (time.time() - self._nav_start_t) > NAV_TIMEOUT_SEC
        return (not self._nav_active and self._nav_result == 'FAILED') or timed_out

    def _cancel_nav(self):
        if self._nav_active:
            self._nav_client._cancel_goal_async()
            self._nav_active = False

    def _transition(self, new_state: MissionState):
        self.get_logger().info(f'{self._state.value} → {new_state.value}')
        self._state      = new_state
        self._nav_active = False
        self._nav_result = None

    def _make_pose(self, wp: dict) -> PoseStamped:
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp    = self.get_clock().now().to_msg()
        pose.pose.position.x = float(wp['x'])
        pose.pose.position.y = float(wp['y'])
        yaw = float(wp.get('yaw', 0.0))
        pose.pose.orientation.z = math.sin(yaw / 2.0)
        pose.pose.orientation.w = math.cos(yaw / 2.0)
        return pose


def main(args=None):
    rclpy.init(args=args)
    node = MissionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
