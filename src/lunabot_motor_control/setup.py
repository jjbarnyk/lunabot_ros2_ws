from setuptools import find_packages, setup

package_name = 'lunabot_motor_control'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Lunabot Team',
    maintainer_email='team@lunabot.local',
    description='Motor control node for Lunabot CAN bus differential drive',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'motor_control_node = lunabot_motor_control.motor_control_node:main',
            'odometry_node = lunabot_motor_control.odometry_node:main',
        ],
    },
)
