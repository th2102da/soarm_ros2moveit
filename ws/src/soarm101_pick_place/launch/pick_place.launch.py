"""ArUco Pick & Place 전체 시스템 launch

포함:
  1. SO-ARM101 MoveIt demo (controllers + move_group + RViz)
  2. Camera bridge (shm → ROS2)
  3. ArUco detector
  4. Pick & Place node

Usage:
  ros2 launch soarm101_pick_place pick_place.launch.py hardware_type:=mock_components
  ros2 launch soarm101_pick_place pick_place.launch.py hardware_type:=real
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
)
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_dir = get_package_share_directory("soarm101_pick_place")
    moveit_pkg = get_package_share_directory("so_arm101_moveit_config")

    intrinsics = os.path.join(pkg_dir, "config", "camera_intrinsics.yaml")
    hand_eye = os.path.join(pkg_dir, "config", "cam_to_robot.yaml")

    hardware_type_arg = DeclareLaunchArgument(
        "hardware_type", default_value="mock_components"
    )

    # 1) MoveIt demo
    moveit_demo = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            os.path.join(moveit_pkg, "launch", "demo.launch.py")
        ),
        launch_arguments=[
            ("hardware_type", LaunchConfiguration("hardware_type")),
        ],
    )

    # 2) Camera bridge
    camera_node = Node(
        package="soarm101_pick_place",
        executable="camera_bridge_node.py",
        name="camera_bridge",
        parameters=[{"intrinsics_file": intrinsics}],
        output="screen",
    )

    # 3) ArUco detector
    aruco_node = Node(
        package="soarm101_pick_place",
        executable="aruco_detector_node.py",
        name="aruco_detector",
        parameters=[
            {"marker_size": 0.03},
            {"intrinsics_file": intrinsics},
            {"hand_eye_file": hand_eye},
            {"aruco_dict": "DICT_4X4_50"},
        ],
        output="screen",
    )

    # 4) Pick & Place
    pick_place_node = Node(
        package="soarm101_pick_place",
        executable="pick_place_node.py",
        name="pick_place",
        output="screen",
    )

    return LaunchDescription([
        hardware_type_arg,
        moveit_demo,
        camera_node,
        aruco_node,
        pick_place_node,
    ])
