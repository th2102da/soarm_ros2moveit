#!/usr/bin/env python3
"""SO-ARM101 MoveIt2 Pose Goal 예제 — Cartesian 좌표로 이동

이 예제는 moveit_py를 사용합니다 (ros-jazzy-moveit-py 필요).

Usage:
  1. demo launch 실행:
     ros2 launch so_arm101_moveit_config demo.launch.py hardware_type:=mock_components

  2. 별도 터미널에서 실행:
     python3 examples/moveit_pose_goal.py

Note: moveit_py가 설치되어 있어야 합니다.
  sudo apt install ros-jazzy-moveit-py (없으면)
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import (
    MotionPlanRequest,
    PlanningOptions,
    Constraints,
    PositionConstraint,
    OrientationConstraint,
    BoundingVolume,
)
from shape_msgs.msg import SolidPrimitive
from rclpy.action import ActionClient
import math


class PoseGoalExample(Node):
    def __init__(self):
        super().__init__("pose_goal_example")
        self._action_client = ActionClient(self, MoveGroup, "move_action")
        self.get_logger().info("Pose Goal Example 시작")

    def send_pose_goal(self, x: float, y: float, z: float,
                       qx: float = 0.0, qy: float = 0.0,
                       qz: float = 0.0, qw: float = 1.0):
        """End-effector를 목표 위치/자세로 이동"""
        self._action_client.wait_for_server()

        goal = MoveGroup.Goal()
        goal.request = MotionPlanRequest()
        goal.request.group_name = "manipulator"
        goal.request.num_planning_attempts = 10
        goal.request.allowed_planning_time = 5.0

        constraints = Constraints()

        # Position constraint
        pos_constraint = PositionConstraint()
        pos_constraint.header.frame_id = "world"
        pos_constraint.link_name = "gripper_link"
        pos_constraint.target_point_offset.x = 0.0
        pos_constraint.target_point_offset.y = 0.0
        pos_constraint.target_point_offset.z = 0.0

        # Bounding region (작은 구)
        bv = BoundingVolume()
        sphere = SolidPrimitive()
        sphere.type = SolidPrimitive.SPHERE
        sphere.dimensions = [0.01]  # 1cm 허용 오차
        bv.primitives.append(sphere)

        target_pose = PoseStamped()
        target_pose.header.frame_id = "world"
        target_pose.pose.position.x = x
        target_pose.pose.position.y = y
        target_pose.pose.position.z = z
        bv.primitive_poses.append(target_pose.pose)
        pos_constraint.constraint_region = bv
        pos_constraint.weight = 1.0
        constraints.position_constraints.append(pos_constraint)

        # Orientation constraint
        ori_constraint = OrientationConstraint()
        ori_constraint.header.frame_id = "world"
        ori_constraint.link_name = "gripper_link"
        ori_constraint.orientation.x = qx
        ori_constraint.orientation.y = qy
        ori_constraint.orientation.z = qz
        ori_constraint.orientation.w = qw
        ori_constraint.absolute_x_axis_tolerance = 0.1
        ori_constraint.absolute_y_axis_tolerance = 0.1
        ori_constraint.absolute_z_axis_tolerance = 0.1
        ori_constraint.weight = 1.0
        constraints.orientation_constraints.append(ori_constraint)

        goal.request.goal_constraints.append(constraints)
        goal.planning_options = PlanningOptions()
        goal.planning_options.plan_only = False

        self.get_logger().info(f"Pose 목표 전송: ({x:.3f}, {y:.3f}, {z:.3f})")
        future = self._action_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future)

        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("목표 거부!")
            return False

        self.get_logger().info("실행 중...")
        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)

        result = result_future.result().result
        success = result.error_code.val == 1
        if success:
            self.get_logger().info("Pose 이동 완료!")
        else:
            self.get_logger().error(f"실패: error_code={result.error_code.val}")
        return success


def main():
    rclpy.init()
    node = PoseGoalExample()

    try:
        # SO-ARM101 작업 공간 내 다양한 위치로 이동 테스트
        # 참고: 로봇 크기가 작으므로 좌표값도 작음 (단위: m)

        # 위치 1: 앞쪽 중앙
        node.send_pose_goal(x=0.15, y=0.0, z=0.15)

        # 위치 2: 왼쪽
        node.send_pose_goal(x=0.10, y=0.10, z=0.10)

        # 위치 3: 오른쪽
        node.send_pose_goal(x=0.10, y=-0.10, z=0.10)

    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
