from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    
    cloud_to_scan = Node(
        package='pointcloud_to_laserscan',
        executable='pointcloud_to_laserscan_node',
        name='cloud_to_scan',
        remappings=[('cloud_in', '/cloud_registered')],
        parameters=[{
            'target_frame': 'camera_init',
            'transform_tolerance': 0.01,
            'min_height': 0.1,
            'max_height': 0.8,
            'angle_min': -3.14159,
            'angle_max': 3.14159,
            'angle_increment': 0.00872,
            'scan_time': 0.1,
            'range_min': 0.3,
            'range_max': 30.0,
            'use_inf': True,
        }]
    )

    slam = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        parameters=[{
            'use_sim_time': False,
            'base_frame': 'body',
            'odom_frame': 'camera_init',
            'map_frame': 'map',
            'scan_topic': '/scan',
            'mode': 'mapping',
            'max_laser_range': 30.0,
            'resolution': 0.05,
            'minimum_travel_distance': 0.1,
            'minimum_travel_heading': 0.1,
        }]
    )

    return LaunchDescription([cloud_to_scan, slam])
