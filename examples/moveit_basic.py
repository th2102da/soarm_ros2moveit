#!/usr/bin/env python3
"""SO-ARM101 MoveIt2 Python 기본 예제

Usage:
  1. 먼저 demo launch를 실행:
     ros2 launch so_arm101_moveit_config demo.launch.py hardware_type:=mock_components

  2. 별도 터미널에서 이 스크립트 실행:
     python3 examples/moveit_basic.py
"""

import rclpy
from rclpy.node import Node
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import (
    MotionPlanRequest,
    PlanningOptions,
    Constraints,
    JointConstraint,
)
from rclpy.action import ActionClient


class MoveItBasicExample(Node):
    def __init__(self):
        super().__init__("moveit_basic_example")
        self._action_client = ActionClient(self, MoveGroup, "move_action")
        self.get_logger().info("MoveIt Basic Example Node 시작")

    def send_joint_goal(self, joint_values: dict):
        """조인트 각도로 로봇을 이동시킵니다.

        Args:
            joint_values: {"shoulder_pan_joint": 0.0, ...} 형태의 딕셔너리
        """
        self.get_logger().info("move_action 서버 대기 중...")
        self._action_client.wait_for_server()

        goal = MoveGroup.Goal()
        goal.request = MotionPlanRequest()
        goal.request.group_name = "manipulator"
        goal.request.num_planning_attempts = 10
        goal.request.allowed_planning_time = 5.0

        # Joint constraints
        constraints = Constraints()
        for joint_name, value in joint_values.items():
            jc = JointConstraint()
            jc.joint_name = joint_name
            jc.position = value
            jc.tolerance_above = 0.01
            jc.tolerance_below = 0.01
            jc.weight = 1.0
            constraints.joint_constraints.append(jc)

        goal.request.goal_constraints.append(constraints)
        goal.planning_options = PlanningOptions()
        goal.planning_options.plan_only = False  # plan + execute

        self.get_logger().info(f"목표 전송: {joint_values}")
        future = self._action_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future)

        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("목표가 거부되었습니다!")
            return

        self.get_logger().info("목표가 수락되었습니다. 실행 중...")
        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)

        result = result_future.result().result
        if result.error_code.val == 1:  # SUCCESS
            self.get_logger().info("이동 완료!")
        else:
            self.get_logger().error(f"이동 실패: error_code={result.error_code.val}")


def main():
    rclpy.init()
    node = MoveItBasicExample()

    try:
        # 1) Zero 포즈로 이동
        node.get_logger().info("=== Zero 포즈로 이동 ===")
        node.send_joint_goal(
            {
                "shoulder_pan_joint": 0.0,
                "shoulder_lift_joint": 0.0,
                "elbow_flex_joint": 0.0,
                "wrist_flex_joint": 0.0,
                "wrist_roll_joint": 0.0,
            }
        )

        # 2) Extended 포즈로 이동
        node.get_logger().info("=== Extended 포즈로 이동 ===")
        node.send_joint_goal(
            {
                "shoulder_pan_joint": 0.0,
                "shoulder_lift_joint": 1.57,
                "elbow_flex_joint": -1.57,
                "wrist_flex_joint": -1.57,
                "wrist_roll_joint": 1.57,
            }
        )

        # 3) Rest 포즈로 이동
        node.get_logger().info("=== Rest 포즈로 이동 ===")
        node.send_joint_goal(
            {
                "shoulder_pan_joint": 0.0,
                "shoulder_lift_joint": -1.75,
                "elbow_flex_joint": 1.57,
                "wrist_flex_joint": -0.35,
                "wrist_roll_joint": 1.57,
            }
        )

    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
