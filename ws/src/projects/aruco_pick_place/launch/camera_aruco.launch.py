"""카메라 + ArUco 감지만 실행 (MoveIt 없이)

카메라/감지 파이프라인만 테스트할 때 사용.

Usage:
  ros2 launch soarm101_pick_place camera_aruco.launch.py
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    pkg_dir = get_package_share_directory("soarm101_pick_place")
    intrinsics = os.path.join(pkg_dir, "config", "camera_intrinsics.yaml")
    hand_eye = os.path.join(pkg_dir, "config", "cam_to_robot.yaml")

    camera_node = Node(
        package="soarm101_pick_place",
        executable="camera_bridge_node.py",
        name="camera_bridge",
        parameters=[{"intrinsics_file": intrinsics}],
        output="screen",
    )

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

    return LaunchDescription([camera_node, aruco_node])
