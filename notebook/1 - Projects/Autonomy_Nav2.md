# Autonomy — Nav2 Integration

## Goal
Wire `mission_node.py` state machine to a working Nav2 stack so the robot can autonomously navigate to a goal pose and return.

## Current State
`mission_node.py` has the full state machine and Nav2 action client calls written. Needs Nav2 running with a valid map and tuned costmap.

## Mission States
```
IDLE → NAVIGATE_OUT → AT_TARGET → NAVIGATE_HOME → DONE
                                      ↓
                                   ABORTED / NAV_FAILED (any state)
```

## What Needs Doing

### Nav2 Stack
- [ ] Add `nav2_bringup` launch to `lunabot_full.launch.py`
- [ ] Configure `nav2_params.yaml` (footprint, costmap, planner)
- [ ] Provide saved map (`.pgm` + `.yaml`) from Point-LIO

### Waypoints
Set in `mission_node.py` after mapping:
```python
HOME_ZONE   = {'x': 0.0, 'y': 0.0, 'yaw': 0.0}
TARGET_ZONE = {'x': 5.0, 'y': 0.0, 'yaw': 0.0}  # ← update this
```
Get coords: echo `/odom` while robot is at the target spot.

### Timeouts / Tuning
- Nav timeout: `NAV_TIMEOUT_SEC = 120.0`
- Dwell at target: `DWELL_AT_TARGET_SEC = 3.0`

## Start / Abort
```bash
ros2 topic pub /mission/start std_msgs/Bool "data: true" --once
ros2 topic pub /mission/abort std_msgs/Bool "data: true" --once
```

## State Monitor
```bash
ros2 topic echo /mission/state
```
