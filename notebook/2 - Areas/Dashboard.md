# Dashboard

Static HTML/JS teleoperation UI in `dashboard/`.

## Connect
1. Start `rosbridge_server` on robot
2. Open `dashboard/index.html` in browser
3. Connects to `ws://localhost:9090`

## Controls
| Key | Action |
|-----|--------|
| W | Forward |
| S | Backward |
| A | Turn left |
| D | Turn right |
| Space | Stop |

## Topics
| Direction | Topic | Type |
|-----------|-------|------|
| Read | `/odom` | Odometry |
| Read | `/scan` | LaserScan |
| Write | `/cmd_vel` | Twist |

## Start ROS Bridge
```bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
```

## Notes
- Dashboard is pure client-side — no build step
- Works over LAN; change `localhost` to robot IP for remote use
