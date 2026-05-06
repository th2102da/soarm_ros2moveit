"""디지털 트윈 Launch: 실제 로봇 + Gazebo 동기화

실제 SO-ARM101 → joint_states → Gazebo 로봇 미러링
Gazebo에 테이블 + 물체 배치

Usage:
  ros2 launch soarm101_pick_place digital_twin.launch.py
  ros2 launch soarm101_pick_place digital_twin.launch.py usb_port:=/dev/ttyACM0
"""

import os

from ament_index_python.packages import get_package_share_directory, get_package_share_path
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.descriptions import ParameterFile
from nav2_common.launch import ReplaceString

from so_arm_utils.launch_utils import load_xacro


def generate_launch_description():
    so_arm_gz_dir = get_package_share_directory("so_arm_gz")
    desc_dir = get_package_share_path("so_arm101_description")

    usb_port_arg = DeclareLaunchArgument("usb_port", default_value="/dev/ttyACM0")

    # ========== 1) 실제 로봇 드라이버 (namespace: /real) ==========
    real_robot_description = load_xacro(
        desc_dir / "urdf" / "so_arm101.urdf.xacro",
        mappings={
            "prefix": "",
            "ros2_control_hardware_type": "real",
            "usb_port": "/dev/ttyACM0",
        },
    )

    real_controllers_file = os.path.join(desc_dir, "control", "ros2_controllers.yaml")
    real_controllers_file_replaced = ReplaceString(
        source_file=real_controllers_file,
        replacements={"<robot_namespace>": ""},
    )

    real_robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        namespace="real",
        parameters=[{"robot_description": real_robot_description}],
    )

    real_control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        namespace="real",
        parameters=[ParameterFile(real_controllers_file_replaced, allow_substs=True)],
        remappings=[("~/robot_description", "/real/robot_description")],
        output="screen",
    )

    real_jsb_spawner = Node(
        package="controller_manager",
        executable="spawner",
        namespace="real",
        arguments=["joint_state_broadcaster"],
    )

    # ========== 2) Gazebo 시뮬레이션 ==========
    gazebo_bringup = IncludeLaunchDescription(
        AnyLaunchDescriptionSource(
            os.path.join(so_arm_gz_dir, "launch", "so_arm_gz_bringup.launch.py")
        ),
        launch_arguments={
            "arm_id": "so_arm101",
            "initial_joint_controller": "forward_position_controller",
            "launch_rviz": "true",
        }.items(),
    )

    # ========== 3) Twin Bridge (real → gazebo) ==========
    twin_bridge = Node(
        package="soarm101_pick_place",
        executable="gz_05_digital_twin.py",
        name="digital_twin_bridge",
        output="screen",
    )

    # ========== 4) 물체 스폰 (지연 실행) ==========
    spawn_objects = TimerAction(
        period=8.0,
        actions=[
            Node(
                package="soarm101_pick_place",
                executable="spawn_objects.py",
                name="spawn_objects",
                output="screen",
            ),
        ],
    )

    return LaunchDescription([
        usb_port_arg,
        # Gazebo
        gazebo_bringup,
        # Real robot
        real_robot_state_publisher,
        real_control_node,
        # Delayed: spawners + bridge + objects (wait for controllers)
        TimerAction(period=3.0, actions=[real_jsb_spawner]),
        TimerAction(period=5.0, actions=[twin_bridge]),
        spawn_objects,
    ])
