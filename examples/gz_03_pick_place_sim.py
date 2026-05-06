#!/usr/bin/env python3
"""예제 3: Pick & Place 시뮬레이션 (Gazebo 물리)

Gazebo에 큐브를 스폰하고, MoveIt으로 잡기→들기→이동→놓기 수행.
그리퍼가 실제로 물체에 힘을 가함 (물리 시뮬레이션).

물체 스폰은 Gazebo 서비스로, 로봇 제어는 MoveIt으로.
"""

import time
import subprocess

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import (
    MotionPlanRequest, PlanningOptions, Constraints, JointConstraint,
    CollisionObject, PlanningScene, PlanningSceneWorld,
)
from control_msgs.action import GripperCommand
from shape_msgs.msg import SolidPrimitive
from geometry_msgs.msg import Pose
from std_msgs.msg import Header


# 조인트 포즈 정의
HOME = {
    "shoulder_pan_joint": 0.0,
    "shoulder_lift_joint": -0.52,
    "elbow_flex_joint": 1.05,
    "wrist_flex_joint": -0.52,
    "wrist_roll_joint": 0.0,
}

ABOVE_PICK = {
    "shoulder_pan_joint": 0.0,
    "shoulder_lift_joint": 1.0,
    "elbow_flex_joint": -1.0,
    "wrist_flex_joint": -1.2,
    "wrist_roll_joint": 0.0,
}

PICK_DOWN = {
    "shoulder_pan_joint": 0.0,
    "shoulder_lift_joint": 1.3,
    "elbow_flex_joint": -1.2,
    "wrist_flex_joint": -1.3,
    "wrist_roll_joint": 0.0,
}

ABOVE_PLACE = {
    "shoulder_pan_joint": -1.2,
    "shoulder_lift_joint": 1.0,
    "elbow_flex_joint": -1.0,
    "wrist_flex_joint": -1.2,
    "wrist_roll_joint": 0.0,
}

PLACE_DOWN = {
    "shoulder_pan_joint": -1.2,
    "shoulder_lift_joint": 1.3,
    "elbow_flex_joint": -1.2,
    "wrist_flex_joint": -1.3,
    "wrist_roll_joint": 0.0,
}


class PickPlaceSimDemo(Node):
    def __init__(self):
        super().__init__("pick_place_sim_demo")
        self._move_client = ActionClient(self, MoveGroup, "move_action")
        self._gripper_client = ActionClient(
            self, GripperCommand, "/gripper_controller/gripper_cmd"
        )
        self._scene_pub = self.create_publisher(PlanningScene, "/planning_scene", 10)
        time.sleep(1.0)

    def move_to(self, name, joints):
        self.get_logger().info(f"  Move: {name}")
        self._move_client.wait_for_server()

        goal = MoveGroup.Goal()
        goal.request = MotionPlanRequest()
        goal.request.group_name = "manipulator"
        goal.request.num_planning_attempts = 10
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

        future = self._move_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future, timeout_sec=10.0)
        gh = future.result()
        if not gh or not gh.accepted:
            self.get_logger().error(f"  {name}: rejected")
            return False
        rf = gh.get_result_async()
        rclpy.spin_until_future_complete(self, rf, timeout_sec=30.0)
        r = rf.result()
        ok = r and r.result.error_code.val == 1
        self.get_logger().info(f"  {name}: {'OK' if ok else 'FAIL'}")
        return ok

    def gripper(self, position, label=""):
        self.get_logger().info(f"  Gripper: {label} ({position:.1f})")
        if not self._gripper_client.wait_for_server(timeout_sec=3.0):
            self.get_logger().warn("  Gripper server not available")
            return
        goal = GripperCommand.Goal()
        goal.command.position = position
        goal.command.max_effort = 10.0
        future = self._gripper_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)
        time.sleep(0.5)

    def add_table(self):
        """Planning scene에 테이블 추가"""
        co = CollisionObject()
        co.header = Header(frame_id="world")
        co.id = "table"
        co.operation = CollisionObject.ADD
        box = SolidPrimitive(type=SolidPrimitive.BOX, dimensions=[0.30, 0.40, 0.01])
        co.primitives.append(box)
        p = Pose()
        p.position.x = 0.15
        p.position.z = -0.01
        p.orientation.w = 1.0
        co.primitive_poses.append(p)

        scene = PlanningScene()
        scene.is_diff = True
        scene.world = PlanningSceneWorld()
        scene.world.collision_objects.append(co)
        self._scene_pub.publish(scene)
        self.get_logger().info("Added table to planning scene")

    def spawn_cube_in_gazebo(self):
        """Gazebo에 큐브 스폰 (gz service 사용)"""
        sdf = """<?xml version="1.0" ?>
<sdf version="1.8">
  <model name="pick_cube">
    <pose>0.12 0 0.025 0 0 0</pose>
    <link name="link">
      <inertial>
        <mass>0.05</mass>
        <inertia>
          <ixx>0.0000083</ixx><iyy>0.0000083</iyy><izz>0.0000083</izz>
        </inertia>
      </inertial>
      <collision name="collision">
        <geometry><box><size>0.03 0.03 0.03</size></box></geometry>
      </collision>
      <visual name="visual">
        <geometry><box><size>0.03 0.03 0.03</size></box></geometry>
        <material>
          <ambient>1 0 0 1</ambient>
          <diffuse>1 0 0 1</diffuse>
        </material>
      </visual>
    </link>
  </model>
</sdf>"""

        try:
            result = subprocess.run(
                ["gz", "service", "-s", "/world/empty/create",
                 "--reqtype", "gz.msgs.EntityFactory",
                 "--reptype", "gz.msgs.Boolean",
                 "--timeout", "5000",
                 "--req", f'sdf: "{sdf.replace(chr(10), " ").replace(chr(34), chr(92)+chr(34))}"'],
                capture_output=True, text=True, timeout=10
            )
            self.get_logger().info(f"Cube spawn: {result.stdout.strip() or 'sent'}")
        except Exception as e:
            self.get_logger().warn(f"Could not spawn cube via gz service: {e}")
            self.get_logger().info("(큐브는 Gazebo GUI에서 직접 추가해도 됩니다)")


def main():
    rclpy.init()
    node = PickPlaceSimDemo()

    node.get_logger().info("=== Pick & Place Simulation Demo ===")

    # 0) 환경 설정
    node.get_logger().info("\n[Phase 0] 환경 설정")
    node.add_table()
    node.spawn_cube_in_gazebo()
    time.sleep(2.0)

    # 1) Home
    node.get_logger().info("\n[Phase 1] Home 이동")
    node.gripper(1.2, "OPEN")
    node.move_to("home", HOME)
    time.sleep(1.0)

    # 2) Pick: 접근 → 하강 → 잡기
    node.get_logger().info("\n[Phase 2] Pick")
    node.move_to("above_pick", ABOVE_PICK)
    time.sleep(0.5)
    node.move_to("pick_down", PICK_DOWN)
    time.sleep(0.5)
    node.gripper(0.0, "CLOSE")
    time.sleep(1.0)

    # 3) Lift
    node.get_logger().info("\n[Phase 3] Lift")
    node.move_to("above_pick", ABOVE_PICK)
    time.sleep(0.5)

    # 4) Transport
    node.get_logger().info("\n[Phase 4] Transport")
    node.move_to("above_place", ABOVE_PLACE)
    time.sleep(0.5)

    # 5) Place: 하강 → 놓기
    node.get_logger().info("\n[Phase 5] Place")
    node.move_to("place_down", PLACE_DOWN)
    time.sleep(0.5)
    node.gripper(1.2, "OPEN")
    time.sleep(1.0)

    # 6) Retreat
    node.get_logger().info("\n[Phase 6] Retreat")
    node.move_to("above_place", ABOVE_PLACE)
    time.sleep(0.5)

    # 7) Home
    node.get_logger().info("\n[Phase 7] Home 복귀")
    node.move_to("home", HOME)

    node.get_logger().info("\n=== Pick & Place Demo 완료 ===")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
