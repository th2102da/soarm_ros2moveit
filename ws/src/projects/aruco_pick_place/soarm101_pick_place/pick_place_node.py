#!/usr/bin/env python3
"""ArUco 기반 Pick & Place 노드

감지된 ArUco 마커 위치로 MoveIt2를 사용해 pick & place 수행.

마커 ID별 동작:
  - ID 0~3: 물체 위치 (pick 대상)
  - 모든 물체를 지정된 place 위치로 이동

Usage:
  # 터미널 1: MoveIt demo
  ros2 launch soarm101_pick_place pick_place.launch.py hardware_type:=mock_components

  # 터미널 2: 이 노드
  ros2 run soarm101_pick_place pick_place_node.py
"""

import time

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseArray, Pose, PoseStamped
from moveit_msgs.action import MoveGroup, ExecuteTrajectory
from moveit_msgs.msg import (
    MotionPlanRequest,
    PlanningOptions,
    Constraints,
    JointConstraint,
    PositionConstraint,
    OrientationConstraint,
    BoundingVolume,
    RobotState,
)
from shape_msgs.msg import SolidPrimitive
from control_msgs.action import GripperCommand
from std_msgs.msg import Header


# SO-ARM101 작업 공간 내 안전한 포즈들 (joint angles in radians)
HOME_JOINTS = {
    "shoulder_pan_joint": 0.0,
    "shoulder_lift_joint": -0.52,  # -30 deg
    "elbow_flex_joint": 1.05,     # 60 deg
    "wrist_flex_joint": -0.52,    # -30 deg
    "wrist_roll_joint": 0.0,
}

# Place 위치 (로봇 좌표계, 여러 빈)
PLACE_POSITIONS = {
    0: {"x": 0.15, "y":  0.10, "z": 0.05},  # 왼쪽 앞
    1: {"x": 0.15, "y": -0.10, "z": 0.05},  # 오른쪽 앞
    2: {"x": 0.10, "y":  0.15, "z": 0.05},  # 왼쪽
    3: {"x": 0.10, "y": -0.15, "z": 0.05},  # 오른쪽
}
DEFAULT_PLACE = {"x": 0.15, "y": -0.10, "z": 0.05}

# 접근 높이 (물체 위 이 높이까지 먼저 이동)
APPROACH_HEIGHT = 0.06  # 6cm above
GRASP_HEIGHT = 0.02     # 2cm above (실제 잡는 높이)


class PickPlaceNode(Node):
    def __init__(self):
        super().__init__("pick_place_node")

        # MoveIt action client
        self._move_client = ActionClient(self, MoveGroup, "move_action")

        # Gripper action client
        self._gripper_client = ActionClient(
            self, GripperCommand, "/gripper_controller/gripper_cmd"
        )

        # Subscribe to detected markers
        self.aruco_sub = self.create_subscription(
            PoseArray, "/aruco/poses", self._aruco_callback, 5
        )

        # State
        self.detected_poses = []
        self.is_busy = False

        # Main loop timer (1 Hz check)
        self.timer = self.create_timer(1.0, self._main_loop)

        self.get_logger().info("Pick & Place node started. Waiting for markers...")

    def _aruco_callback(self, msg):
        if msg.poses:
            self.detected_poses = msg.poses

    def _main_loop(self):
        if self.is_busy:
            return

        if not self.detected_poses:
            return

        # Pick the first detected object
        target = self.detected_poses[0]
        x, y, z = target.position.x, target.position.y, target.position.z

        # Sanity check - is it in workspace?
        if not (-0.05 < x < 0.35 and -0.25 < y < 0.25 and 0.0 < z < 0.30):
            self.get_logger().warn(
                f"Target ({x:.3f}, {y:.3f}, {z:.3f}) outside workspace, skipping"
            )
            self.detected_poses = []
            return

        self.get_logger().info(f"Starting pick at ({x:.3f}, {y:.3f}, {z:.3f})")
        self.is_busy = True

        try:
            self._execute_pick_place(x, y, z)
        except Exception as e:
            self.get_logger().error(f"Pick & place failed: {e}")
        finally:
            self.is_busy = False
            self.detected_poses = []

    def _execute_pick_place(self, x, y, z):
        """전체 pick & place 시퀀스"""

        # 1) Open gripper
        self.get_logger().info("Step 1: Open gripper")
        self._send_gripper(1.2)  # open

        # 2) Move to approach (above target)
        self.get_logger().info("Step 2: Approach")
        if not self._move_to_joints(HOME_JOINTS):
            self.get_logger().error("Failed to move to home")
            return

        # 3) Move above target
        self.get_logger().info("Step 3: Move above target")
        approach_joints = self._compute_approach_joints(x, y, z + APPROACH_HEIGHT)
        if approach_joints and not self._move_to_joints(approach_joints):
            self.get_logger().warn("Approach via joints failed, trying home first")

        # 4) Lower to grasp height
        self.get_logger().info("Step 4: Lower to grasp")
        grasp_joints = self._compute_approach_joints(x, y, z + GRASP_HEIGHT)
        if grasp_joints:
            self._move_to_joints(grasp_joints)

        # 5) Close gripper
        self.get_logger().info("Step 5: Close gripper")
        self._send_gripper(0.0)  # close
        time.sleep(0.5)

        # 6) Lift
        self.get_logger().info("Step 6: Lift")
        lift_joints = self._compute_approach_joints(x, y, z + APPROACH_HEIGHT + 0.05)
        if lift_joints:
            self._move_to_joints(lift_joints)

        # 7) Move to place position
        self.get_logger().info("Step 7: Move to place")
        place = DEFAULT_PLACE
        place_joints = self._compute_approach_joints(
            place["x"], place["y"], place["z"] + APPROACH_HEIGHT
        )
        if place_joints:
            self._move_to_joints(place_joints)

        # 8) Lower and release
        self.get_logger().info("Step 8: Lower and release")
        lower_joints = self._compute_approach_joints(
            place["x"], place["y"], place["z"] + GRASP_HEIGHT
        )
        if lower_joints:
            self._move_to_joints(lower_joints)

        self._send_gripper(1.2)  # open
        time.sleep(0.3)

        # 9) Retreat and go home
        self.get_logger().info("Step 9: Return home")
        self._move_to_joints(HOME_JOINTS)

        self.get_logger().info("Pick & place complete!")

    def _compute_approach_joints(self, x, y, z):
        """간단한 기하학적 IK로 접근 조인트 계산 (MoveIt에 의존하지 않는 fallback)

        실제 MoveIt IK를 사용하려면 move_group의 compute_ik 서비스를 호출해야 하지만,
        여기서는 간단한 2-link planar approximation을 사용.
        """
        import math

        # SO-ARM101 링크 길이 (URDF에서 추출)
        L1 = 0.11257  # upper arm
        L2 = 0.1349   # lower arm
        L3 = 0.061    # wrist to gripper

        # Base rotation
        shoulder_pan = math.atan2(y, x)

        # Distance in XY plane from base
        r = math.sqrt(x**2 + y**2)
        # Target height relative to shoulder
        # Shoulder is at approximately z=0.062 from base
        z_shoulder = z - 0.062

        # Distance from shoulder to target (2D: r, z_shoulder)
        target_dist = math.sqrt(r**2 + z_shoulder**2)

        # Check reachability
        max_reach = L1 + L2
        if target_dist > max_reach * 0.95:
            self.get_logger().warn(f"Target too far: {target_dist:.3f}m > {max_reach:.3f}m")
            return None

        # 2-link IK (shoulder_lift + elbow)
        cos_elbow = (target_dist**2 - L1**2 - L2**2) / (2 * L1 * L2)
        cos_elbow = np.clip(cos_elbow, -1, 1)
        elbow = -math.acos(cos_elbow)  # elbow down

        # Shoulder lift
        alpha = math.atan2(z_shoulder, r)
        beta = math.atan2(L2 * math.sin(-elbow), L1 + L2 * math.cos(-elbow))
        shoulder_lift = alpha + beta

        # Wrist: keep gripper pointing down
        wrist_flex = -(shoulder_lift + elbow) - math.pi/2

        # Clamp to joint limits
        shoulder_pan = np.clip(shoulder_pan, -1.92, 1.92)
        shoulder_lift = np.clip(shoulder_lift, -1.75, 1.75)
        elbow = np.clip(elbow, -1.69, 1.54)
        wrist_flex = np.clip(wrist_flex, -1.6, 1.6)

        return {
            "shoulder_pan_joint": shoulder_pan,
            "shoulder_lift_joint": shoulder_lift,
            "elbow_flex_joint": elbow,
            "wrist_flex_joint": wrist_flex,
            "wrist_roll_joint": 0.0,
        }

    def _move_to_joints(self, joint_values: dict) -> bool:
        """MoveIt으로 조인트 목표 이동"""
        if not self._move_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error("MoveGroup action server not available")
            return False

        goal = MoveGroup.Goal()
        goal.request = MotionPlanRequest()
        goal.request.group_name = "manipulator"
        goal.request.num_planning_attempts = 5
        goal.request.allowed_planning_time = 3.0

        constraints = Constraints()
        for name, value in joint_values.items():
            jc = JointConstraint()
            jc.joint_name = name
            jc.position = float(value)
            jc.tolerance_above = 0.01
            jc.tolerance_below = 0.01
            jc.weight = 1.0
            constraints.joint_constraints.append(jc)

        goal.request.goal_constraints.append(constraints)
        goal.planning_options = PlanningOptions()
        goal.planning_options.plan_only = False

        future = self._move_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future, timeout_sec=10.0)

        goal_handle = future.result()
        if not goal_handle or not goal_handle.accepted:
            self.get_logger().error("Goal rejected")
            return False

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future, timeout_sec=15.0)

        result = result_future.result()
        if result and result.result.error_code.val == 1:
            return True
        self.get_logger().warn(f"Motion failed: {result.result.error_code.val if result else 'timeout'}")
        return False

    def _send_gripper(self, position: float):
        """그리퍼 제어 (0=closed, 1.2=open)"""
        if not self._gripper_client.wait_for_server(timeout_sec=3.0):
            self.get_logger().warn("Gripper action server not available")
            return

        goal = GripperCommand.Goal()
        goal.command.position = position
        goal.command.max_effort = 10.0

        future = self._gripper_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)


def main(args=None):
    rclpy.init(args=args)
    node = PickPlaceNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
