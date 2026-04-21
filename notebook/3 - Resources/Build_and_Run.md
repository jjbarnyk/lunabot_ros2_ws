# Build & Run

## Build

```bash
# Full workspace
colcon build --symlink-install
source install/setup.bash

# Single package
colcon build --symlink-install --packages-select <package_name>
```

If `livox_ros_driver2` is installed, source it first:
```bash
source /path/to/livox_ros_driver2/install/setup.bash
colcon build --symlink-install
```

Custom PCL (add to `~/.bashrc`):
```bash
export PCL_ROOT={CUSTOM_PCL_PATH}
```

## Launch

```bash
# SLAM with Unitree L1
ros2 launch point_lio_ros2 mapping_unilidar_l1.launch.py

# Robot description / TF tree
ros2 launch lunabot_description description.launch.py

# Full system
ros2 launch lunabot_bringup lunabot_full.launch.py
```

## Run Individual Nodes

```bash
ros2 run lunabot_motor_control motor_control_node
ros2 run lunabot_motor_control odometry_node
```

## CAN Bus Setup (Pi)

```bash
sudo ip link set can0 up type can bitrate 1000000
```

Add to `/etc/network/interfaces` or systemd unit for persistence.

## Useful Debug Commands

```bash
# Watch odometry
ros2 topic echo /odom

# Watch mission state
ros2 topic echo /mission/state

# Send velocity command
ros2 topic pub /cmd_vel geometry_msgs/Twist "{linear: {x: 0.2}, angular: {z: 0.0}}" --once

# E-stop
ros2 topic pub /estop std_msgs/Bool "data: true" --once

# TF tree
ros2 run tf2_tools view_frames
```
