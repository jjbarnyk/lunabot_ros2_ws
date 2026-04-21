# Robot Description (URDF)

**Package:** `lunabot_description`
**URDF:** `src/lunabot_description/urdf/lunabot.urdf`

## Launch
```bash
ros2 launch lunabot_description description.launch.py
```
Publishes TF tree and robot_description parameter.

## Geometry

| Dimension | Value |
|-----------|-------|
| Wheel base (track width) | 0.58 m |
| Wheel radius | 0.15 m |
| LiDAR mount height | 0.225 m above base_link |
| LiDAR position | rear-center of chassis |

## Frames
- `base_link` — robot center
- `lidar_link` — Unitree L1 mount point (0, 0, 0.225 from base_link)
- `wheel_*_link` — four wheels

## Notes
Geometry values must stay in sync with:
- `motor_control_node.py` (`WHEEL_BASE`, `WHEEL_RADIUS`)
- `odometry_node.py` (`WHEEL_BASE`, `WHEEL_RADIUS`)
