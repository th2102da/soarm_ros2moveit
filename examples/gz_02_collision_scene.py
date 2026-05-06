#!/usr/bin/env python3
"""예제 2: Collision Scene — 테이블 + 장애물 배치 후 충돌 회피 경로 계획

MoveIt planning scene에 테이블과 장애물을 추가하고,
로봇이 장애물을 피해서 목표에 도달하는 경로를 계획/실행.
"""

import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import (
    MotionPlanRequest, PlanningOptions, Constraints, JointConstraint,
    CollisionObject, PlanningScene, PlanningSceneWorld,
)
from shape_msgs.msg import SolidPrimitive
from geometry_msgs.msg import Pose, PoseStamped
from std_msgs.msg import Header


class CollisionSceneDemo(Node):
    def __init__(self):
        super().__init__("collision_scene_demo")
        self._move_client = ActionClient(self, MoveGroup, "move_action")
        self._scene_pub = self.create_publisher(
            PlanningScene, "/planning_scene", 10
        )
        time.sleep(1.0)  # publisher 연결 대기

    def add_box(self, name, x, y, z, sx, sy, sz):
        """Planning scene에 박스 장애물 추가"""
        co = CollisionObject()
        co.header = Header(frame_id="world")
        co.id = name
        co.operation = CollisionObject.ADD

        box = SolidPrimitive()
        box.type = SolidPrimitive.BOX
        box.dimensions = [sx, sy, sz]
        co.primitives.append(box)

        pose = Pose()
        pose.position.x = x
        pose.position.y = y
        pose.position.z = z
        pose.orientation.w = 1.0
        co.primitive_poses.append(pose)

        scene = PlanningScene()
        scene.is_diff = True
        scene.world = PlanningSceneWorld()
        scene.world.collision_objects.append(co)
        self._scene_pub.publish(scene)
        self.get_logger().info(f"Added '{name}' at ({x:.2f}, {y:.2f}, {z:.2f}) size ({sx:.2f}, {sy:.2f}, {sz:.2f})")

    def remove_all(self):
        """모든 collision object 제거"""
        for name in ["table", "wall", "obstacle"]:
            co = CollisionObject()
            co.header = Header(frame_id="world")
            co.id = name
            co.operation = CollisionObject.REMOVE

            scene = PlanningScene()
            scene.is_diff = True
            scene.world = PlanningSceneWorld()
            scene.world.collision_objects.append(co)
            self._scene_pub.publish(scene)

        self.get_logger().info("Removed all collision objects")

    def move_to(self, name, joints):
        self.get_logger().info(f">>> Moving to '{name}'")
        self._move_client.wait_for_server()

        goal = MoveGroup.Goal()
        goal.request = MotionPlanRequest()
        goal.request.group_name = "manipulator"
        goal.request.num_planning_attempts = 10
        goal.request.allowed_planning_time = 10.0

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

        future = self._move_client.send_goal_async(goal)
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
    node = CollisionSceneDemo()
    time.sleep(1.0)

    # 1) 테이블 추가 (로봇 앞에 큰 평면)
    node.get_logger().info("=== Step 1: 장애물 배치 ===")
    node.add_box("table",   0.15, 0.0, -0.02,  0.30, 0.40, 0.02)  # 테이블
    node.add_box("wall",    0.10, 0.15, 0.10,   0.20, 0.02, 0.20)  # 벽 (왼쪽)
    node.add_box("obstacle", 0.12, -0.05, 0.08, 0.04, 0.04, 0.08)  # 장애물
    time.sleep(2.0)

    # 2) 시작: zero 포즈
    node.get_logger().info("=== Step 2: Zero 포즈 ===")
    node.move_to("zero", {
        "shoulder_pan_joint": 0.0,
        "shoulder_lift_joint": 0.0,
        "elbow_flex_joint": 0.0,
        "wrist_flex_joint": 0.0,
        "wrist_roll_joint": 0.0,
    })
    time.sleep(1.0)

    # 3) 장애물 뒤쪽 목표 — MoveIt이 장애물 피해서 경로 생성
    node.get_logger().info("=== Step 3: 장애물 피해서 오른쪽으로 ===")
    node.move_to("right_side", {
        "shoulder_pan_joint": -1.0,
        "shoulder_lift_joint": 0.5,
        "elbow_flex_joint": -0.5,
        "wrist_flex_joint": -0.5,
        "wrist_roll_joint": 0.0,
    })
    time.sleep(1.0)

    # 4) 왼쪽 벽 너머로 — 벽 위로 지나가야 함
    node.get_logger().info("=== Step 4: 왼쪽 벽 너머로 ===")
    node.move_to("left_side", {
        "shoulder_pan_joint": 1.2,
        "shoulder_lift_joint": 0.8,
        "elbow_flex_joint": -0.8,
        "wrist_flex_joint": -0.5,
        "wrist_roll_joint": 0.0,
    })
    time.sleep(1.0)

    # 5) 원위치
    node.get_logger().info("=== Step 5: Zero 복귀 ===")
    node.move_to("zero", {
        "shoulder_pan_joint": 0.0,
        "shoulder_lift_joint": 0.0,
        "elbow_flex_joint": 0.0,
        "wrist_flex_joint": 0.0,
        "wrist_roll_joint": 0.0,
    })

    # 6) 장애물 제거
    node.get_logger().info("=== Step 6: 정리 ===")
    time.sleep(1.0)
    node.remove_all()

    node.get_logger().info("=== Collision Scene Demo 완료 ===")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
