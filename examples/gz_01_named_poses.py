#!/usr/bin/env python3
"""예제 1: Named Poses — Gazebo에서 사전 정의 자세로 이동

SRDF에 정의된 zero, extended, rest 포즈로 순차 이동.
Gazebo에서 물리 시뮬레이션으로 실제처럼 움직임.
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import MotionPlanRequest, PlanningOptions, Constraints, JointConstraint

NAMED_POSES = {
    "zero": {
        "shoulder_pan_joint": 0.0,
        "shoulder_lift_joint": 0.0,
        "elbow_flex_joint": 0.0,
        "wrist_flex_joint": 0.0,
        "wrist_roll_joint": 0.0,
    },
    "extended": {
        "shoulder_pan_joint": 0.0,
        "shoulder_lift_joint": 1.57,
        "elbow_flex_joint": -1.57,
        "wrist_flex_joint": -1.57,
        "wrist_roll_joint": 1.57,
    },
    "rest": {
        "shoulder_pan_joint": 0.0,
        "shoulder_lift_joint": -1.75,
        "elbow_flex_joint": 1.57,
        "wrist_flex_joint": -0.35,
        "wrist_roll_joint": 1.57,
    },
}


class NamedPosesDemo(Node):
    def __init__(self):
        super().__init__("named_poses_demo")
        self._client = ActionClient(self, MoveGroup, "move_action")

    def move_to(self, name, joints):
        self.get_logger().info(f">>> Moving to '{name}'")
        self._client.wait_for_server()

        goal = MoveGroup.Goal()
        goal.request = MotionPlanRequest()
        goal.request.group_name = "manipulator"
        goal.request.num_planning_attempts = 5
        goal.request.allowed_planning_time = 5.0

        c = Constraints()
        for jname, val in joints.items():
            jc = JointConstraint()
            jc.joint_name = jname
            jc.position = val
            jc.tolerance_above = 0.01
            jc.tolerance_below = 0.01
            jc.weight = 1.0
            c.joint_constraints.append(jc)
        goal.request.goal_constraints.append(c)

        goal.planning_options = PlanningOptions()
        goal.planning_options.plan_only = False

        future = self._client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future, timeout_sec=10.0)
        gh = future.result()
        if not gh or not gh.accepted:
            self.get_logger().error("Goal rejected!")
            return False

        result_future = gh.get_result_async()
        rclpy.spin_until_future_complete(self, result_future, timeout_sec=30.0)
        result = result_future.result()
        ok = result and result.result.error_code.val == 1
        self.get_logger().info(f"    {'SUCCESS' if ok else 'FAILED'}")
        return ok


def main():
    rclpy.init()
    node = NamedPosesDemo()

    import time
    for name in ["zero", "extended", "rest", "zero"]:
        node.move_to(name, NAMED_POSES[name])
        time.sleep(1.0)

    node.get_logger().info("=== Named Poses Demo 완료 ===")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
