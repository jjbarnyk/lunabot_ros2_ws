// ==============================
// Lunabot Dashboard — app.js
// Manual + Autonomous mode
// ==============================

const CONFIG = {
  rosbridgeUrl:    'ws://192.168.0.100:9090',
  cmdVelTopic:     '/cmd_vel',
  odomTopic:       '/odom',
  scanTopic:       '/scan',
  missionStart:    '/mission/start',
  missionAbort:    '/mission/abort',
  missionState:    '/mission/state',
  estopTopic:      '/estop',
};

// ── ROS connection ────────────────────────────────────────────────────────────
const ros = new ROSLIB.Ros({ url: CONFIG.rosbridgeUrl });

const statusEl = document.getElementById('status');

ros.on('connection', () => {
  statusEl.textContent = '✓ Connected to ROS2';
  statusEl.className = 'status connected';
  initTopics();
});

ros.on('error', () => {
  statusEl.textContent = '✗ Connection error';
  statusEl.className = 'status disconnected';
});

ros.on('close', () => {
  statusEl.textContent = '✗ Disconnected';
  statusEl.className = 'status disconnected';
});

// ── Topics ────────────────────────────────────────────────────────────────────
let cmdVel        = null;
let missionStart  = null;
let missionAbort  = null;
let estopPub      = null;

function initTopics() {

  // cmd_vel publisher
  cmdVel = new ROSLIB.Topic({
    ros, name: CONFIG.cmdVelTopic,
    messageType: 'geometry_msgs/Twist'
  });

  // mission/start publisher
  missionStart = new ROSLIB.Topic({
    ros, name: CONFIG.missionStart,
    messageType: 'std_msgs/Bool'
  });

  // mission/abort publisher
  missionAbort = new ROSLIB.Topic({
    ros, name: CONFIG.missionAbort,
    messageType: 'std_msgs/Bool'
  });

  // estop publisher
  estopPub = new ROSLIB.Topic({
    ros, name: CONFIG.estopTopic,
    messageType: 'std_msgs/Bool'
  });

  // odom subscriber
  const odom = new ROSLIB.Topic({
    ros, name: CONFIG.odomTopic,
    messageType: 'nav_msgs/Odometry',
    throttle_rate: 100
  });
  odom.subscribe((msg) => {
    document.getElementById('pos-x').textContent =
      msg.pose.pose.position.x.toFixed(2);
    document.getElementById('pos-y').textContent =
      msg.pose.pose.position.y.toFixed(2);
    document.getElementById('vel-x').textContent =
      msg.twist.twist.linear.x.toFixed(2);
  });

  // scan subscriber
  const scan = new ROSLIB.Topic({
    ros, name: CONFIG.scanTopic,
    messageType: 'sensor_msgs/LaserScan',
    throttle_rate: 100
  });
  scan.subscribe((msg) => {
    const valid = msg.ranges.filter(r => Number.isFinite(r) && r > 0);
    if (valid.length > 0) {
      document.getElementById('closest-obj').textContent =
        Math.min(...valid).toFixed(2);
    }
  });

  // mission state subscriber
  const missionStateTopic = new ROSLIB.Topic({
    ros, name: CONFIG.missionState,
    messageType: 'std_msgs/String',
    throttle_rate: 200
  });
  missionStateTopic.subscribe((msg) => {
    document.getElementById('mission-state').textContent = msg.data;
  });
}

// ── Mode switching ────────────────────────────────────────────────────────────
let currentMode = 'manual';

function setMode(mode) {
  currentMode = mode;

  // Update buttons
  document.querySelector('.mode-btn.manual').classList.toggle('active', mode === 'manual');
  document.querySelector('.mode-btn.autonomous').classList.toggle('active', mode === 'autonomous');

  // Show/hide panels
  document.getElementById('manual-panel').classList.toggle('hidden', mode !== 'manual');
  document.getElementById('auto-panel').classList.toggle('hidden', mode !== 'autonomous');

  // Update mode display
  document.getElementById('mode-display').textContent = mode.toUpperCase();

  // Stop robot when switching modes
  sendVelocity(0, 0);

  console.log('Mode switched to:', mode);
}

// ── Velocity commands ─────────────────────────────────────────────────────────
function sendVelocity(linear, angular) {
  if (!cmdVel) return;
  if (currentMode !== 'manual') return;  // block driving in autonomous mode

  cmdVel.publish(new ROSLIB.Message({
    linear:  { x: linear,  y: 0.0, z: 0.0 },
    angular: { x: 0.0,     y: 0.0, z: angular }
  }));
}

window.sendVelocity = sendVelocity;

// ── Mission controls ──────────────────────────────────────────────────────────
function startMission() {
  if (!missionStart) return;
  missionStart.publish(new ROSLIB.Message({ data: true }));
  console.log('Mission started');
}

function abortMission() {
  if (!missionAbort) return;
  missionAbort.publish(new ROSLIB.Message({ data: true }));
  console.log('Mission aborted');
}

function eStop() {
  if (!estopPub) return;
  estopPub.publish(new ROSLIB.Message({ data: true }));
  sendVelocity(0, 0);
  console.log('E-STOP activated');
}

window.startMission = startMission;
window.abortMission = abortMission;
window.eStop        = eStop;

// ── Keyboard control (manual mode only) ──────────────────────────────────────
document.addEventListener('keydown', (e) => {
  if (e.repeat) return;
  if (currentMode !== 'manual') return;

  switch (e.key.toLowerCase()) {
    case 'w': sendVelocity( 0.3,  0.0); break;
    case 's': sendVelocity(-0.3,  0.0); break;
    case 'a': sendVelocity( 0.0,  0.5); break;
    case 'd': sendVelocity( 0.0, -0.5); break;
    case ' ':
      e.preventDefault();
      sendVelocity(0.0, 0.0);
      break;
  }
});

document.addEventListener('keyup', (e) => {
  if (['w','a','s','d',' '].includes(e.key.toLowerCase())) {
    sendVelocity(0.0, 0.0);
  }
});
