const ros = new ROSLIB.Ros({ url: 'ws://localhost:9090' });
const statusEl = document.getElementById('status');

ros.on('connection', () => {
	statusEl.textContent = '✓ Connected';
	statusEl.className = 'connected';
	initTopics();
});
ros.on('error',  (e) => { statusEl.textContent = '✗ Error: ' + e; statusEl.className = 'disconnected'; });
ros.on('close',  ()  => { statusEl.textContent = '✗ Closed'; statusEl.className = 'disconnected'; });

let cmdVel;

function initTopics() {
	// Subscribe to odometry
	const odom = new ROSLIB.Topic({
		ros, name: '/odom',
		messageType: 'nav_msgs/Odometry',
		throttle_rate: 100
	});
	odom.subscribe((msg) => {
		document.getElementById('ox').textContent =
			msg.pose.pose.position.x.toFixed(3) + ' m';
		document.getElementById('oy').textContent =
			msg.pose.pose.position.y.toFixed(3) + ' m';
		document.getElementById('vx').textContent =
			msg.twist.twist.linear.x.toFixed(3) + ' m/s';
	});

	// Publisher
	cmdVel = new ROSLIB.Topic({
		ros, name: '/cmd_vel',
		messageType: 'geometry_msgs/Twist'
	});
}

function drive(linear, angular) {
	if (!cmdVel) return;
	cmdVel.publish(new ROSLIB.Message({
		linear:  { x: linear,  y: 0, z: 0 },
		angular: { x: 0, y: 0, z: angular }
	}));
}
