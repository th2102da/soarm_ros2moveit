"""SO-ARM101 제어 라이브러리 — 학생용

이 파일은 수정하지 않아도 됩니다.
로봇 팔을 쉽게 제어할 수 있는 함수들을 제공합니다.

사용법:
    from robot_arm import RobotArm
    arm = RobotArm()
    arm.home()
    arm.move_joints(shoulder_pan=0.5, shoulder_lift=1.0, ...)
    arm.gripper_open()
    arm.gripper_close()
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
from sensor_msgs.msg import JointState


class RobotArm(Node):
    def __init__(self, name="robot_arm"):
        super().__init__(name)
        self._move_client = ActionClient(self, MoveGroup, "move_action")
        self._gripper_client = ActionClient(
            self, GripperCommand, "/gripper_controller/gripper_cmd"
        )
        self._scene_pub = self.create_publisher(PlanningScene, "/planning_scene", 10)

        # 현재 조인트 상태 구독
        self._joint_positions = {}
        self._joint_sub = self.create_subscription(
            JointState, "/joint_states", self._joint_cb, 10
        )

        time.sleep(0.5)
        self.get_logger().info("RobotArm 준비 완료")

    def _joint_cb(self, msg):
        self._joint_positions = dict(zip(msg.name, msg.position))

    def get_joint_positions(self):
        """현재 조인트 각도 반환"""
        rclpy.spin_once(self, timeout_sec=0.1)
        return self._joint_positions.copy()

    # ─── 이동 ──────────────────────────────────────

    def move_joints(self, shoulder_pan=0.0, shoulder_lift=0.0,
                    elbow_flex=0.0, wrist_flex=0.0, wrist_roll=0.0):
        """조인트 각도(radian)로 이동

        각 조인트 범위:
            shoulder_pan:  -1.92 ~ 1.92 (base 회전)
            shoulder_lift: -1.75 ~ 1.75 (어깨)
            elbow_flex:    -1.69 ~ 1.54 (팔꿈치)
            wrist_flex:    -1.60 ~ 1.60 (손목 굽힘)
            wrist_roll:    -2.30 ~ 2.30 (손목 회전)

        Returns: True(성공) / False(실패)
        """
        joints = {
            "shoulder_pan_joint": shoulder_pan,
            "shoulder_lift_joint": shoulder_lift,
            "elbow_flex_joint": elbow_flex,
            "wrist_flex_joint": wrist_flex,
            "wrist_roll_joint": wrist_roll,
        }

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
            jc.position = float(val)
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
            self.get_logger().warn("모션 플래닝 실패")
            return False

        rf = gh.get_result_async()
        rclpy.spin_until_future_complete(self, rf, timeout_sec=30.0)
        r = rf.result()
        return r and r.result.error_code.val == 1

    def home(self):
        """안전한 홈 위치"""
        self.get_logger().info("→ HOME")
        return self.move_joints(0.0, -0.5, 1.0, -0.5, 0.0)

    def zero(self):
        """모든 조인트 0도"""
        self.get_logger().info("→ ZERO")
        return self.move_joints()

    # ─── 그리퍼 ─────────────────────────────────────

    def gripper_open(self):
        """그리퍼 열기"""
        self._send_gripper(1.2)

    def gripper_close(self):
        """그리퍼 닫기 (물체 잡기)"""
        self._send_gripper(0.0)

    def _send_gripper(self, position):
        if not self._gripper_client.wait_for_server(timeout_sec=2.0):
            return
        goal = GripperCommand.Goal()
        goal.command.position = position
        goal.command.max_effort = 10.0
        future = self._gripper_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)
        time.sleep(0.3)

    # ─── Gazebo 물체 관리 ────────────────────────────

    def spawn_box(self, name, x, y, z, size=0.03, r=1.0, g=0.0, b=0.0, mass=0.03):
        """Gazebo에 박스 물체 생성"""
        ixx = mass * (size**2 + size**2) / 12
        sdf = f"""<?xml version="1.0" ?>
<sdf version="1.8"><model name="{name}">
  <pose>{x} {y} {z} 0 0 0</pose>
  <link name="link">
    <inertial><mass>{mass}</mass>
      <inertia><ixx>{ixx:.8f}</ixx><iyy>{ixx:.8f}</iyy><izz>{ixx:.8f}</izz></inertia>
    </inertial>
    <collision name="c"><geometry><box><size>{size} {size} {size}</size></box></geometry>
      <surface><friction><ode><mu>1</mu><mu2>1</mu2></ode></friction></surface>
    </collision>
    <visual name="v"><geometry><box><size>{size} {size} {size}</size></box></geometry>
      <material><ambient>{r} {g} {b} 1</ambient><diffuse>{r} {g} {b} 1</diffuse></material>
    </visual>
  </link>
</model></sdf>"""
        self._gz_spawn(name, sdf)

    def spawn_table(self, x=0.15, y=0.0):
        """테이블 생성"""
        sdf = f"""<?xml version="1.0" ?>
<sdf version="1.8"><model name="table"><static>true</static>
  <pose>{x} {y} 0.005 0 0 0</pose>
  <link name="link">
    <collision name="c"><geometry><box><size>0.35 0.50 0.01</size></box></geometry></collision>
    <visual name="v"><geometry><box><size>0.35 0.50 0.01</size></box></geometry>
      <material><ambient>0.55 0.35 0.15 1</ambient><diffuse>0.55 0.35 0.15 1</diffuse></material>
    </visual>
  </link>
</model></sdf>"""
        self._gz_spawn("table", sdf)

    def spawn_zone(self, name, x, y, r, g, b):
        """분류 영역 표시 (바닥 색깔 패드)"""
        sdf = f"""<?xml version="1.0" ?>
<sdf version="1.8"><model name="{name}"><static>true</static>
  <pose>{x} {y} 0.001 0 0 0</pose>
  <link name="link">
    <visual name="v"><geometry><box><size>0.06 0.06 0.002</size></box></geometry>
      <material><ambient>{r} {g} {b} 1</ambient><diffuse>{r} {g} {b} 1</diffuse></material>
    </visual>
  </link>
</model></sdf>"""
        self._gz_spawn(name, sdf)

    def _gz_spawn(self, name, sdf):
        sdf_clean = sdf.replace("\n", " ").replace('"', '\\"')
        try:
            subprocess.run(
                ["gz", "service", "-s", "/world/empty/create",
                 "--reqtype", "gz.msgs.EntityFactory",
                 "--reptype", "gz.msgs.Boolean",
                 "--timeout", "5000",
                 "--req", f'sdf: "{sdf_clean}"'],
                capture_output=True, text=True, timeout=10,
            )
        except Exception:
            pass

    # ─── Planning Scene (충돌 물체) ──────────────────

    def add_collision_box(self, name, x, y, z, sx, sy, sz):
        """MoveIt planning scene에 충돌 박스 추가 (RViz에서 보임)"""
        co = CollisionObject()
        co.header = Header(frame_id="world")
        co.id = name
        co.operation = CollisionObject.ADD
        box = SolidPrimitive(type=SolidPrimitive.BOX, dimensions=[sx, sy, sz])
        co.primitives.append(box)
        p = Pose()
        p.position.x, p.position.y, p.position.z = x, y, z
        p.orientation.w = 1.0
        co.primitive_poses.append(p)
        scene = PlanningScene()
        scene.is_diff = True
        scene.world = PlanningSceneWorld()
        scene.world.collision_objects.append(co)
        self._scene_pub.publish(scene)

    def remove_collision(self, name):
        """Planning scene에서 충돌 물체 제거"""
        co = CollisionObject()
        co.header = Header(frame_id="world")
        co.id = name
        co.operation = CollisionObject.REMOVE
        scene = PlanningScene()
        scene.is_diff = True
        scene.world = PlanningSceneWorld()
        scene.world.collision_objects.append(co)
        self._scene_pub.publish(scene)
