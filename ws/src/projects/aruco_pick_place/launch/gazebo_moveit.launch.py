"""Gazebo + MoveIt2 통합 launch

Gazebo 물리 시뮬레이션 + MoveIt2 move_group + RViz를 한 번에 실행.

Usage:
  ros2 launch soarm101_pick_place gazebo_moveit.launch.py
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch_ros.actions import Node

from so_arm_utils.launch_utils import MoveItConfigs


def generate_launch_description():
    so_arm_gz_dir = get_package_share_directory("so_arm_gz")
    moveit_config_dir = get_package_share_directory("so_arm101_moveit_config")

    # 1) Gazebo + ros2_control (no RViz from here)
    gazebo_bringup = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            os.path.join(so_arm_gz_dir, "launch", "so_arm_gz_bringup.launch.py")
        ),
        launch_arguments={
            "arm_id": "so_arm101",
            "initial_joint_controller": "joint_trajectory_controller",
            "launch_rviz": "false",
        }.items(),
    )

    # 2) MoveIt move_group
    moveit_configs = MoveItConfigs(robot_name="so_arm101")
    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        parameters=[
            moveit_configs.to_dict(),
            {"use_sim_time": True},
        ],
    )

    # 3) RViz with MoveIt plugin
    from launch.substitutions import PathJoinSubstitution
    from launch_ros.substitutions import FindPackageShare

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        arguments=[
            "-d",
            os.path.join(moveit_config_dir, "rviz", "move_group.rviz"),
        ],
        parameters=[
            moveit_configs.joint_limits,
            moveit_configs.robot_description,
            moveit_configs.robot_description_semantic,
            moveit_configs.robot_description_kinematics,
            moveit_configs.planning_pipelines,
            {"use_sim_time": True},
        ],
    )

    return LaunchDescription([
        gazebo_bringup,
        move_group_node,
        rviz_node,
    ])
