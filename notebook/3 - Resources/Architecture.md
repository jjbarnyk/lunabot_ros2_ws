# System Architecture

## Packages

| Package | Type | Purpose |
|---------|------|---------|
| `lunabot_motor_control` | Python (ament_python) | SPARK MAX CAN driver + wheel odometry |
| `lunabot_autonomy` | Python (ament_python) | Mission state machine, Nav2 client |
| `lunabot_description` | ament_cmake | URDF robot model, TF publishers |
| `lunabot_bringup` | Python | Launch files |
| `point_lio_ros2` | ament_cmake (C++) | LiDAR-Inertial SLAM |
| `unilidar_sdk` | C++ + ROS2 | Unitree LiDAR L1/L2 driver |
| `dashboard` | Plain JS | Web teleoperation UI |

## Control Flow

```
Dashboard (ws://<robot>:9090) ─┐
Keyboard / teleop               ├──► /cmd_vel ──► motor_control_node ──► CAN ──► SPARK MAX
Mission node (Nav2)            ─┘
                                        │
/estop ─────────────────────────────────┘  (watchdog: 0.5s timeout)
```

## Localization Flow

```
Unitree L1 ──► /unilidar/cloud ──► Point-LIO ──► /odometry/odom
           └──► /unilidar/imu ──┘              └──► TF: map → camera_init

SPARK MAX encoders ──► /odom ──► TF: odom → base_link
```

## TF Tree

```
map
 └── camera_init        (Point-LIO SLAM)
      └── odom
           └── base_link    (wheel odometry)
                └── lidar_link
                └── wheel_fl_link
                └── wheel_fr_link
                └── wheel_rl_link
                └── wheel_rr_link
```

## Topic Summary

| Topic | Type | Publisher | Subscribers |
|-------|------|-----------|-------------|
| `/cmd_vel` | Twist | dashboard / mission_node | motor_control_node |
| `/estop` | Bool | dashboard / operator | motor_control_node |
| `/odom` | Odometry | odometry_node | Nav2, dashboard |
| `/odometry/odom` | Odometry | Point-LIO | Nav2 |
| `/unilidar/cloud` | PointCloud2 | unilidar_sdk | Point-LIO |
| `/unilidar/imu` | Imu | unilidar_sdk | Point-LIO |
| `/mission/state` | String | mission_node | dashboard |
| `/mission/start` | Bool | operator | mission_node |
| `/mission/abort` | Bool | operator | mission_node |
