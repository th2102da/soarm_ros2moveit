#!/usr/bin/env python3
"""예제 4: Cartesian Waypoints — 직선 경로로 패턴 그리기

MoveIt의 Cartesian path planning으로 end-effector가
직선 경로를 따라 사각형/원 패턴을 그림.
"""

import math
import time

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import MotionPlanRequest, PlanningOptions, Constraints, JointConstraint
from moveit_msgs.srv import GetCartesianPath
from geometry_msgs.msg import Pose, PoseStamped
from moveit_msgs.action import ExecuteTrajectory


class WaypointsDemo(Node):
    def __init__(self):
        super().__init__("waypoints_demo")
        self._move_client = ActionClient(self, MoveGroup, "move_action")
        self._exec_client = ActionClient(self, ExecuteTrajectory, "execute_trajectory")
        self._cartesian_client = self.create_client(
            GetCartesianPath, "/compute_cartesian_path"
        )

    def move_to_joints(self, name, joints):
        self.get_logger().info(f"Move: {name}")
        self._move_client.wait_for_server()

        goal = MoveGroup.Goal()
        goal.request = MotionPlanRequest()
        goal.request.group_name = "manipulator"
        goal.request.num_planning_attempts = 5
        goal.request.allowed_planning_time = 5.0

        c = Constraints()
        for jn, v in joints.items():
            jc = JointConstraint()
            jc.joint_name = jn
            jc.position = v
            jc.tolerance_above = 0.01
            jc.tolerance_below = 0.01
            jc.weight = 1.0
            c.joint_constraints.append(jc)
        goal.request.goal_constraints.append(c)
        goal.planning_options = PlanningOptions()
        goal.planning_options.plan_only = False

        f = self._move_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, f, timeout_sec=10.0)
        gh = f.result()
        if not gh or not gh.accepted:
            return False
        rf = gh.get_result_async()
        rclpy.spin_until_future_complete(self, rf, timeout_sec=30.0)
        r = rf.result()
        return r and r.result.error_code.val == 1

    def execute_cartesian(self, waypoints, description=""):
        """Cartesian path를 계획하고 실행"""
        self.get_logger().info(f"Cartesian path: {description} ({len(waypoints)} points)")

        if not self._cartesian_client.wait_for_service(timeout_sec=5.0):
            self.get_logger().error("Cartesian path service not available")
            return False

        req = GetCartesianPath.Request()
        req.header.frame_id = "world"
        req.group_name = "manipulator"
        req.link_name = "gripper_link"
        req.max_step = 0.005  # 5mm resolution
        req.avoid_collisions = True

        for wp in waypoints:
            p = Pose()
            p.position.x = wp[0]
            p.position.y = wp[1]
            p.position.z = wp[2]
            p.orientation.x = 0.0
            p.orientation.y = 0.707
            p.orientation.z = 0.0
            p.orientation.w = 0.707
            req.waypoints.append(p)

        future = self._cartesian_client.call_async(req)
        rclpy.spin_until_future_complete(self, future, timeout_sec=10.0)
        result = future.result()

        if result is None:
            self.get_logger().error("Cartesian path planning failed")
            return False

        fraction = result.fraction
        self.get_logger().info(f"  Achieved {fraction*100:.1f}% of path")

        if fraction < 0.5:
            self.get_logger().warn("  Too little path achieved, skipping execution")
            return False

        # Execute
        if not self._exec_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error("Execute trajectory server not available")
            return False

        exec_goal = ExecuteTrajectory.Goal()
        exec_goal.trajectory = result.solution
        ef = self._exec_client.send_goal_async(exec_goal)
        rclpy.spin_until_future_complete(self, ef, timeout_sec=10.0)
        egh = ef.result()
        if not egh or not egh.accepted:
            return False
        erf = egh.get_result_async()
        rclpy.spin_until_future_complete(self, erf, timeout_sec=30.0)
        er = erf.result()
        ok = er and er.result.error_code.val == 1
        self.get_logger().info(f"  Execution: {'OK' if ok else 'FAIL'}")
        return ok


def main():
    rclpy.init()
    node = WaypointsDemo()

    # 시작 자세: 팔을 앞으로 뻗음
    node.get_logger().info("=== Waypoints Demo ===")
    node.move_to_joints("start", {
        "shoulder_pan_joint": 0.0,
        "shoulder_lift_joint": 0.8,
        "elbow_flex_joint": -0.8,
        "wrist_flex_joint": -1.0,
        "wrist_roll_joint": 0.0,
    })
    time.sleep(1.0)

    # 사각형 패턴 — 오리엔테이션 없이 waypoint만 전달
    node.get_logger().info("\n--- 사각형 패턴 (joint space) ---")
    # joint space로 사각형의 4 꼭짓점 이동
    corners = [
        {"shoulder_pan_joint": -0.4, "shoulder_lift_joint": 0.8, "elbow_flex_joint": -0.8, "wrist_flex_joint": -1.0, "wrist_roll_joint": 0.0},
        {"shoulder_pan_joint":  0.4, "shoulder_lift_joint": 0.8, "elbow_flex_joint": -0.8, "wrist_flex_joint": -1.0, "wrist_roll_joint": 0.0},
        {"shoulder_pan_joint":  0.4, "shoulder_lift_joint": 1.2, "elbow_flex_joint": -1.0, "wrist_flex_joint": -1.0, "wrist_roll_joint": 0.0},
        {"shoulder_pan_joint": -0.4, "shoulder_lift_joint": 1.2, "elbow_flex_joint": -1.0, "wrist_flex_joint": -1.0, "wrist_roll_joint": 0.0},
        {"shoulder_pan_joint": -0.4, "shoulder_lift_joint": 0.8, "elbow_flex_joint": -0.8, "wrist_flex_joint": -1.0, "wrist_roll_joint": 0.0},
    ]
    for i, c in enumerate(corners):
        node.move_to_joints(f"corner_{i}", c)
        time.sleep(0.3)
    time.sleep(1.0)

    # 원형 패턴 — joint space sweep
    node.get_logger().info("\n--- 원형 패턴 (shoulder pan sweep) ---")
    circle = []
    for i in range(13):
        angle = -0.6 + 1.2 * i / 12  # -0.6 to 0.6 rad sweep
        circle.append(angle)
    for i, pan in enumerate(circle):
        node.move_to_joints(f"arc_{i}", {
            "shoulder_pan_joint": pan,
            "shoulder_lift_joint": 1.0,
            "elbow_flex_joint": -0.9,
            "wrist_flex_joint": -1.0,
            "wrist_roll_joint": 0.0,
        })
    time.sleep(1.0)

    # 원위치
    node.move_to_joints("home", {
        "shoulder_pan_joint": 0.0,
        "shoulder_lift_joint": 0.0,
        "elbow_flex_joint": 0.0,
        "wrist_flex_joint": 0.0,
        "wrist_roll_joint": 0.0,
    })

    node.get_logger().info("=== Waypoints Demo 완료 ===")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
