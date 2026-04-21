# Motor Control

**Node:** `motor_control_node.py`
**Package:** `lunabot_motor_control`
**Run:** `ros2 run lunabot_motor_control motor_control_node`

## Hardware
- 4× REV SPARK MAX motor controllers
- Connected via CAN bus (`can0`)
- Device IDs set in REV Hardware Client

| Position | Device ID | Notes |
|----------|-----------|-------|
| Front-Left | 1 | — |
| Front-Right | 2 | direction negated |
| Rear-Left | 3 | — |
| Rear-Right | 4 | direction negated |

## CAN Protocol
SPARK MAX uses 29-bit extended CAN IDs.

**Duty cycle command:**
```
Arbitration ID = (0x020 << 6) | device_id
Data = 4-byte little-endian float, range -1.0 to 1.0
```

**Heartbeat** (broadcast, required every 80ms or controllers disable):
```
ID   = 0x2052C80
Data = 0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0xFF
```

## Kinematics (Differential Drive)
```
left_mps  = linear - angular * (wheel_base / 2)
right_mps = linear + angular * (wheel_base / 2)
duty      = wheel_mps / max_linear_speed
```

Parameters:
- Wheel base: `0.58 m`
- Wheel radius: `0.15 m`
- Max speed: `0.5 m/s`

## Subscriptions
| Topic | Type | Purpose |
|-------|------|---------|
| `/cmd_vel` | `Twist` | velocity commands |
| `/estop` | `Bool` | emergency stop |

## Publications
| Topic | Type | Purpose |
|-------|------|---------|
| `/odom` | `Odometry` | dead-reckoning odometry (from cmd_vel integration) |

## Safety
- Watchdog: motors stop if no `/cmd_vel` within **0.5 s**
- E-stop: publish `True` to `/estop` → immediate stop, latches until `False` published
