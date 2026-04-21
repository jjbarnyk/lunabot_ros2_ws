# Localization

Two parallel odometry sources. Point-LIO is primary for autonomous operation.

## Wheel Odometry

**Node:** `odometry_node.py`
**Package:** `lunabot_motor_control`
**Rate:** 50 Hz

Reads encoder tick counts from CAN bus, integrates differential drive kinematics.

### Encoder CAN IDs
| Wheel | CAN ID |
|-------|--------|
| Front-Left | `0x201` |
| Front-Right | `0x202` |
| Rear-Left | `0x203` |
| Rear-Right | `0x204` |

Frame format: bytes 0–3 = `int32` big-endian cumulative tick count.

### Parameters
- Ticks/rev: `4096`
- `metres_per_tick = (2π × 0.15) / 4096 ≈ 0.000230 m`

### Outputs
- `/odom` (Odometry)
- TF: `odom → base_link`

---

## SLAM Odometry — Point-LIO

**Package:** `point_lio_ros2`
**Algorithm:** Iterated Kalman Filter on Manifolds (IKFoM) + ikd-Tree
**Inputs:** LiDAR (`/unilidar/cloud`) + IMU (`/unilidar/imu`)

### Launch
```bash
ros2 launch point_lio_ros2 mapping_unilidar_l1.launch.py
```

### Config
`src/point_lio_ros2/config/unilidar_l1.yaml`
- Voxel filter: `0.1 m`
- IMU acc saturation: `30.0`

### Outputs
- `/odometry/odom` (Odometry)
- TF: `map → camera_init`

### Notes
- Source `livox_ros_driver2` before building if installed
- Custom PCL: `export PCL_ROOT={CUSTOM_PCL_PATH}` in `~/.bashrc`

---

## TF Tree
```
map
 └── camera_init        ← Point-LIO
      └── odom
           └── base_link  ← wheel odometry
```
