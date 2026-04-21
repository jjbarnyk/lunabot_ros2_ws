# Sensor Integration

## Unitree LiDAR L1

**Package:** `unilidar_sdk` (`src/unilidar_sdk/`)
**Driver:** `unitree_lidar_ros2`

### Published Topics
| Topic | Type | Content |
|-------|------|---------|
| `/unilidar/cloud` | `PointCloud2` | 3D point cloud |
| `/unilidar/imu` | `Imu` | IMU data |

### URDF Placement
LiDAR mounted at `base_link` offset: `(0, 0, 0.225 m)` — rear-center of chassis.

### Launch
```bash
# LiDAR driver is included in Point-LIO launch
ros2 launch point_lio_ros2 mapping_unilidar_l1.launch.py

# Driver standalone
ros2 launch unitree_lidar_ros2 launch.py
```

## IMU
Built into Unitree L1 — published on `/unilidar/imu`.
Fused with LiDAR in Point-LIO IKFoM filter.
