# Hardware Reference

## Parameters

| Parameter | Value | Used In |
|-----------|-------|---------|
| Wheel base (track width) | 0.58 m | motor_control_node, odometry_node, URDF |
| Wheel radius | 0.15 m | motor_control_node, odometry_node, URDF |
| Max drive speed | 0.5 m/s | motor_control_node |
| Encoder ticks/rev | 4096 | odometry_node |
| Odometry rate | 50 Hz | odometry_node |
| LiDAR voxel filter | 0.1 m | unilidar_l1.yaml |
| IMU acc saturation | 30.0 | unilidar_l1.yaml |
| CAN heartbeat interval | 80 ms | motor_control_node |
| cmd_vel watchdog timeout | 0.5 s | motor_control_node |

## CAN IDs

### Motor Commands (PC → SPARK MAX)
| Motor | Device ID | Arbitration ID |
|-------|-----------|----------------|
| Front-Left | 1 | `(0x020 << 6) \| 1` = `0x801` |
| Front-Right | 2 | `(0x020 << 6) \| 2` = `0x802` |
| Rear-Left | 3 | `(0x020 << 6) \| 3` = `0x803` |
| Rear-Right | 4 | `(0x020 << 6) \| 4` = `0x804` |

### Encoder Feedback (SPARK MAX → PC)
| Wheel | CAN ID |
|-------|--------|
| Front-Left | `0x201` |
| Front-Right | `0x202` |
| Rear-Left | `0x203` |
| Rear-Right | `0x204` |

### Heartbeat
| Frame | Value |
|-------|-------|
| ID | `0x2052C80` (29-bit extended) |
| Data | `FF FF FF FF FF FF FF FF` |
| Required interval | every 80 ms |

## Network (Field Setup)

| Device | Interface | IP |
|--------|-----------|-----|
| Laptop | WiFi (`wlp0s20f3`) | 10.246.x.x (internet) |
| Laptop | Ethernet (`enp57s0u1u4c2`) | 192.168.0.101 (AP DHCP) |
| Pi (lunabot) | WiFi | 192.168.0.x (AP DHCP) |
| AP | — | 192.168.0.254 (gateway) |

SSH: `ssh jjb@<pi-ip>`
ROS Bridge: `ws://<pi-ip>:9090`
