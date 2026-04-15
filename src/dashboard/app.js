// ==============================
// Lunabot ROS2 Dashboard Config
// ==============================
const CONFIG = {
  rosbridgeUrl: 'ws://localhost:9090',
  cmdVelTopic: '/cmd_vel',
  odomTopic: '/odom',
  scanTopic: '/scan',
  cameraTopic: '/camera/image_raw',
  videoServerBase: 'http://localhost:8080'
};

const ros = new ROSLIB.Ros({
  url: CONFIG.rosbridgeUrl
});

const statusEl = document.getElementById('status');

let cmdVel = null;

// ==============================
// Camera stream setup
// ==============================
function getCameraStreamUrl() {
  return `${CONFIG.videoServerBase}/stream?topic=${CONFIG.cameraTopic}`;
}

const cameraUrl = getCameraStreamUrl();

document.getElementById('camera-feed').src = cameraUrl;
document.getElementById('camera-url').textContent = cameraUrl;

// ==============================
// ROS connection
// ==============================
ros.on('connection', () => {
  statusEl.textContent = '✓ Connected to ROS2';
  statusEl.className = 'status connected';

  console.log('Connected to rosbridge');

  initTopics();
});

ros.on('error', (err) => {
  statusEl.textContent = '✗ Connection error';
  statusEl.className = 'status disconnected';

  console.error('ROS connection error:', err);
});

ros.on('close', () => {
  statusEl.textContent = '✗ Disconnected';
  statusEl.className = 'status disconnected';

  console.log('ROS connection closed');
});

// ==============================
// Initialize ROS topics
// ==============================
function initTopics() {
  // Publisher: /cmd_vel
  cmdVel = new ROSLIB.Topic({
    ros: ros,
    name: CONFIG.cmdVelTopic,
    messageType: 'geometry_msgs/Twist'
  });

  console.log(`${CONFIG.cmdVelTopic} publisher ready`);

  // Subscriber: /odom
  const odomTopic = new ROSLIB.Topic({
    ros: ros,
    name: CONFIG.odomTopic,
    messageType: 'nav_msgs/Odometry',
    throttle_rate: 100
  });

  odomTopic.subscribe((msg) => {
    const x = msg.pose.pose.position.x;
    const y = msg.pose.pose.position.y;
    const vx = msg.twist.twist.linear.x;

    document.getElementById('pos-x').textContent = x.toFixed(2);
    document.getElementById('pos-y').textContent = y.toFixed(2);
    document.getElementById('vel-x').textContent = vx.toFixed(2);
  });

  // Subscriber: /scan
  const scanTopic = new ROSLIB.Topic({
    ros: ros,
    name: CONFIG.scanTopic,
    messageType: 'sensor_msgs/LaserScan',
    throttle_rate: 100
  });

  scanTopic.subscribe((msg) => {
    const validRanges = msg.ranges.filter((r) => Number.isFinite(r));

    if (validRanges.length > 0) {
      const minDist = Math.min(...validRanges);
      document.getElementById('closest-obj').textContent = minDist.toFixed(2);
    }
  });
}

// ==============================
// Publish velocity commands
// ==============================
function sendVelocity(linear, angular) {
  if (!cmdVel) {
    console.log('cmdVel publisher not ready yet');
    return;
  }

  const msg = new ROSLIB.Message({
    linear: {
      x: linear,
      y: 0.0,
      z: 0.0
    },
    angular: {
      x: 0.0,
      y: 0.0,
      z: angular
    }
  });

  cmdVel.publish(msg);

  console.log('Published velocity:', linear, angular);
}

window.sendVelocity = sendVelocity;

// Keep teammate compatibility
function drive(linear, angular) {
  sendVelocity(linear, angular);
}

window.drive = drive;

// ==============================
// Keyboard control
// ==============================
document.addEventListener('keydown', (event) => {
  if (event.repeat) return;

  switch (event.key.toLowerCase()) {
    case 'w':
      sendVelocity(0.3, 0.0);
      break;

    case 's':
      sendVelocity(-0.3, 0.0);
      break;

    case 'a':
      sendVelocity(0.0, 0.5);
      break;

    case 'd':
      sendVelocity(0.0, -0.5);
      break;

    case ' ':
      event.preventDefault();
      sendVelocity(0.0, 0.0);
      break;
  }
});

document.addEventListener('keyup', (event) => {
  const key = event.key.toLowerCase();

  if (['w', 'a', 's', 'd', ' '].includes(key)) {
    sendVelocity(0.0, 0.0);
  }
});

// ==============================
// ROS Info service
// ==============================
const topicService = new ROSLIB.Service({
  ros: ros,
  name: '/rosapi/topics',
  serviceType: 'rosapi_msgs/Topics'
});

function getTopics() {
  topicService.callService(
    new ROSLIB.ServiceRequest(),
    (res) => {
      console.log('ROS topics:', res.topics);
    },
    (err) => {
      console.error('Topic service error:', err);
    }
  );
}

window.getTopics = getTopics;