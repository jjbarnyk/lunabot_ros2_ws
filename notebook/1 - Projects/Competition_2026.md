# NASA Lunabotics 2026 — Competition Prep

## Goal
Robot navigates autonomously from start zone to excavation zone, dwells, returns. Scored on autonomy + reliability.

## Status
- [x] Drive / CAN motor control
- [x] Wheel odometry
- [x] LiDAR SLAM (Point-LIO)
- [x] URDF / TF tree
- [x] Dashboard teleoperation
- [x] Mission state machine (Nav2 skeleton)
- [ ] Full Nav2 integration (costmap, planner tuning)
- [ ] Map saved from competition field
- [ ] TARGET_ZONE waypoint set in `mission_node.py`
- [ ] Field testing end-to-end autonomous run

## Critical Path
1. Build map of competition field with Point-LIO
2. Record target zone coordinates from `/odom`
3. Set `TARGET_ZONE` in `mission_node.py`
4. Tune Nav2 costmap for arena surface
5. Run full autonomous loop in test environment

## Key Files
- `src/lunabot_autonomy/lunabot_autonomy/mission_node.py` — state machine
- `src/point_lio_ros2/config/unilidar_l1.yaml` — SLAM config
- `src/lunabot_bringup/launch/lunabot_full.launch.py` — full system launch
