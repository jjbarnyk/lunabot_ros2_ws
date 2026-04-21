# Lunabot ROS 2 Workspace

Autonomous navigation stack for the NASA Lunabotics competition robot.
**Mission: Drive to target zone → return home.**

Hardware: Raspberry Pi 5 | SPARK MAX x4 | NEO Brushless x4 | Unitree LiDAR L1 | RS485 CAN HAT
Software: ROS 2 Jazzy | Ubuntu 24.04

---

## What This Does

```
IDLE → NAVIGATE TO TARGET → WAIT 3 SECONDS → RETURN HOME → DONE
```

The robot:
1. Waits for your start command
2. Uses LiDAR to see the world
3. Builds or loads a map
4. Plans a path to the target
5. Drives there autonomously avoiding obstacles
6. Comes back home on its own

---

## Package Overview

| Package | What it does |
|---|---|
| `lunabot_motor_control` | Sends CAN commands to SPARK MAX controllers |
| `lunabot_autonomy` | Mission brain — navigate out and back |
| `lunabot_bringup` | One command that starts everything |
| `lunabot_description` | 3D model of the robot (URDF) |
| `point_lio_ros2` | Turns LiDAR data into robot position |
| `unilidar_sdk` | Driver for Unitree LiDAR L1 |
| `dashboard` | Web UI for teleoperation and monitoring |

---

## Before Anything — Configure SPARK MAX Controllers

On a Windows PC using REV Hardware Client (download from revrobotics.com):

Connect each SPARK MAX via USB-C and set:
- Motor Type → NEO Brushless
- Idle Mode → Brake
- Device ID → see table below

| Controller | Device ID |
|---|---|
| Front-Left SPARK MAX | 1 |
| Front-Right SPARK MAX | 2 |
| Rear-Left SPARK MAX | 3 |
| Rear-Right SPARK MAX | 4 |

Do this for all 4 before wiring anything to the Pi.

---

## Setup on Raspberry Pi 5

### Step 1 — Flash Ubuntu 24.04 Server onto SD card
Use Raspberry Pi Imager on Windows. Enable SSH and WiFi in settings.

### Step 2 — SSH into Pi
```bash
ssh ubuntu@lunabot.local
```

### Step 3 — Set up CAN HAT
```bash
sudo nano /boot/firmware/config.txt
```
Add at the bottom:
```
dtparam=spi=on
dtoverlay=mcp2515-can0,oscillator=12000000,interrupt=25
```
```bash
sudo reboot
```

### Step 4 — Bring up CAN bus
```bash
sudo ip link set can0 up type can bitrate 1000000
sudo ip link set can0 txqueuelen 1000
ip link show can0    # verify it says UP
```

### Step 5 — Install everything
```bash
# System tools
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git nano python3-pip can-utils \
  python3-rosdep python3-colcon-common-extensions

# Add ROS 2 Jazzy
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=arm64 signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu noble main" | \
  sudo tee /etc/apt/sources.list.d/ros2.list
sudo apt update
sudo apt install -y ros-jazzy-ros-base ros-dev-tools

# ROS packages
sudo apt install -y \
  ros-jazzy-nav2-bringup \
  ros-jazzy-slam-toolbox \
  ros-jazzy-pointcloud-to-laserscan \
  ros-jazzy-rosbridge-server \
  ros-jazzy-robot-state-publisher \
  ros-jazzy-joint-state-publisher \
  ros-jazzy-tf2-ros \
  ros-jazzy-tf2-tools

# Python CAN for SPARK MAX
pip3 install python-can --break-system-packages

# rosdep
sudo rosdep init
rosdep update

# Auto source ROS
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

### Step 6 — Transfer and build workspace
On your Windows laptop:
```bash
scp lunabot_final_v2.tar.gz ubuntu@lunabot.local:~/
```

On the Pi:
```bash
cd ~
tar -xzf lunabot_final_v2.tar.gz
cd lunabot_ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install --parallel-workers 2
echo "source ~/lunabot_ros2_ws/install/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

Wait 15-20 minutes for build to finish.

### Step 7 — Verify build
```bash
ros2 pkg list | grep lunabot
```
Should show:
```
lunabot_autonomy
lunabot_bringup
lunabot_description
lunabot_motor_control
```

---

## Running the Robot

### Phase 1 — Map the area (do once)
```bash
ros2 launch lunabot_bringup lunabot_full.launch.py mode:=mapping
```
Open browser: `http://lunabot.local:8080`
Drive around with W/A/S/D to build a map.

Save the map:
```bash
ros2 run nav2_map_server map_saver_cli -f ~/lunabot_map
```

### Phase 2 — Set target zone coordinates
Drive robot to the target spot, then:
```bash
ros2 topic echo /odom --once
```
Copy the x and y values. Open:
```bash
nano ~/lunabot_ros2_ws/src/lunabot_autonomy/lunabot_autonomy/mission_node.py
```
Update:
```python
TARGET_ZONE = {'x': YOUR_X, 'y': YOUR_Y, 'yaw': 0.0}
```
Rebuild:
```bash
cd ~/lunabot_ros2_ws
colcon build --packages-select lunabot_autonomy --symlink-install
```

### Phase 3 — Full autonomy
```bash
ros2 launch lunabot_bringup lunabot_full.launch.py \
  mode:=navigation \
  map:=~/lunabot_map.yaml \
  use_mission:=true
```

Start mission:
```bash
ros2 topic pub /mission/start std_msgs/msg/Bool "data: true" --once
```

Emergency stop:
```bash
ros2 topic pub /estop std_msgs/msg/Bool "data: true" --once
```

---

## Debug Commands

```bash
ros2 topic echo /mission/state       # current mission state
ros2 topic echo /odom                # robot position
ros2 topic echo /scan --no-arr       # LiDAR readings
ros2 topic list -t                   # all active topics
ros2 run tf2_tools view_frames       # check transform tree
candump can0                         # raw CAN bus traffic
```

---

## SPARK MAX Configuration in Code

Device IDs are set in:
`src/lunabot_motor_control/lunabot_motor_control/motor_control_node.py`

```python
ID_FRONT_LEFT  = 1   # must match REV Hardware Client
ID_FRONT_RIGHT = 2
ID_REAR_LEFT   = 3
ID_REAR_RIGHT  = 4
MAX_LINEAR_SPEED = 0.5   # tune this to your robot's real max speed (m/s)
```

---

## Checklist Before Competition

- [ ] All 4 SPARK MAXes configured in REV Hardware Client (IDs 1-4, NEO, Brake mode)
- [ ] CAN bus wired and verified with candump
- [ ] Map built and saved
- [ ] TARGET_ZONE coordinates set from real field measurement
- [ ] MAX_LINEAR_SPEED tuned to actual robot speed
- [ ] E-STOP tested and working
- [ ] Full autonomy run tested at least once before competition day
