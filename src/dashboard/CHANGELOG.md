# Lunabot ROS2 Dashboard Change Log

## Dashboard Integration - Initial Merge

### Files changed
- `src/dashboard/index.html`
- `src/dashboard/app.js`

### Features added
- Added full Lunabot dashboard layout
- Added camera feed panel using `web_video_server`
- Added odometry display for X, Y, and linear velocity
- Added closest object display from `/scan`
- Added button-based teleop controls
- Added W/A/S/D keyboard teleop
- Added spacebar stop command
- Added ROS topic list button
- Preserved teammate's `drive(linear, angular)` function compatibility

### Files intentionally not touched
- `point.io`
- `unilidar`

### Notes
- Dashboard connects to rosbridge at `ws://localhost:9090`
- Camera stream assumes `web_video_server` is running at `http://localhost:8080`
- Main velocity command topic is `/cmd_vel`
- Odom topic is `/odom`
- LiDAR topic is `/scan`