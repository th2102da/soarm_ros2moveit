#!/usr/bin/env python3
"""02. Behavior Tree로 Pick & Place

Week 1의 State Machine을 Behavior Tree로 재구현합니다.
트리 구조로 행동을 조합하고, Fallback으로 실패를 처리합니다.

트리 구조:
    [Root: Sequence]
    ├── [Setup]
    │   ├── Home
    │   └── GripperOpen
    ├── [Pick: Sequence]
    │   ├── Approach
    │   ├── Descend
    │   └── GripperClose
    ├── [Place: Sequence]
    │   ├── Lift
    │   ├── Transport
    │   ├── Lower
    │   └── GripperOpen
    └── Home

★ 과제:
  1. 트리에 새로운 행동 추가 (예: 잡기 전 대기)
  2. Fallback으로 실패 시 재시도 구현
"""

import time
import py_trees
import rclpy
from robot_arm import RobotArm


# ============================================================
# 로봇 행동 노드 정의
# ============================================================

class MoveJoints(py_trees.behaviour.Behaviour):
    """로봇을 지정된 조인트 각도로 이동"""
    def __init__(self, name, arm, **joints):
        super().__init__(name)
        self.arm = arm
        self.joints = joints

    def update(self):
        print(f"    → {self.name}")
        ok = self.arm.move_joints(**self.joints)
        return py_trees.common.Status.SUCCESS if ok else py_trees.common.Status.FAILURE


class GripperAction(py_trees.behaviour.Behaviour):
    """그리퍼 열기/닫기"""
    def __init__(self, name, arm, open=True):
        super().__init__(name)
        self.arm = arm
        self.open = open

    def update(self):
        if self.open:
            self.arm.gripper_open()
        else:
            self.arm.gripper_close()
        time.sleep(0.3)
        print(f"    → {self.name}")
        return py_trees.common.Status.SUCCESS


class SpawnObject(py_trees.behaviour.Behaviour):
    """Gazebo에 물체 스폰"""
    def __init__(self, name, arm):
        super().__init__(name)
        self.arm = arm
        self.done = False

    def update(self):
        if not self.done:
            self.arm.spawn_table()
            time.sleep(0.3)
            self.arm.spawn_box("cube", 0.12, 0.0, 0.025, r=1, g=0, b=0)
            self.arm.spawn_zone("target", 0.05, 0.18, 1, 0.3, 0.3)
            time.sleep(0.5)
            self.done = True
            print("    → 환경 배치 완료")
        return py_trees.common.Status.SUCCESS


class Wait(py_trees.behaviour.Behaviour):
    """잠시 대기"""
    def __init__(self, name, seconds=0.5):
        super().__init__(name)
        self.seconds = seconds

    def update(self):
        time.sleep(self.seconds)
        return py_trees.common.Status.SUCCESS


# ============================================================
# 조인트 각도 설정
# ============================================================

PICK_ABOVE = dict(shoulder_pan=0.0, shoulder_lift=1.0, elbow_flex=-0.9,
                  wrist_flex=-1.1, wrist_roll=0.0)
PICK_DOWN  = dict(shoulder_pan=0.0, shoulder_lift=1.35, elbow_flex=-1.15,
                  wrist_flex=-1.3, wrist_roll=0.0)
PLACE_ABOVE = dict(shoulder_pan=1.3, shoulder_lift=1.0, elbow_flex=-0.9,
                   wrist_flex=-1.1, wrist_roll=0.0)
PLACE_DOWN  = dict(shoulder_pan=1.3, shoulder_lift=1.35, elbow_flex=-1.15,
                   wrist_flex=-1.3, wrist_roll=0.0)
HOME = dict(shoulder_pan=0.0, shoulder_lift=-0.5, elbow_flex=1.0,
            wrist_flex=-0.5, wrist_roll=0.0)


# ============================================================
# Behavior Tree 구성
# ============================================================

def create_pick_place_tree(arm):
    """Pick & Place Behavior Tree 생성"""

    # Setup
    setup = py_trees.composites.Sequence("Setup", memory=True)
    setup.add_children([
        SpawnObject("환경배치", arm),
        MoveJoints("Home", arm, **HOME),
        GripperAction("그리퍼열기", arm, open=True),
    ])

    # Pick
    pick = py_trees.composites.Sequence("Pick", memory=True)
    pick.add_children([
        MoveJoints("접근", arm, **PICK_ABOVE),
        MoveJoints("내려가기", arm, **PICK_DOWN),
        GripperAction("잡기", arm, open=False),
        Wait("잡기대기", 0.5),
    ])

    # Place
    place = py_trees.composites.Sequence("Place", memory=True)
    place.add_children([
        MoveJoints("들기", arm, **PICK_ABOVE),
        MoveJoints("이동", arm, **PLACE_ABOVE),
        MoveJoints("내려놓기", arm, **PLACE_DOWN),
        GripperAction("놓기", arm, open=True),
        MoveJoints("후퇴", arm, **PLACE_ABOVE),
    ])

    # Root
    root = py_trees.composites.Sequence("PickAndPlace", memory=True)
    root.add_children([
        setup,
        pick,
        place,
        MoveJoints("Home복귀", arm, **HOME),
    ])

    return root


# ============================================================
# 메인
# ============================================================

def main():
    rclpy.init()
    arm = RobotArm()

    print("=" * 50)
    print("  Behavior Tree: Pick & Place")
    print("=" * 50)

    # 트리 생성
    root = create_pick_place_tree(arm)
    tree = py_trees.trees.BehaviourTree(root)

    # 트리 구조 출력
    print("\n트리 구조:")
    print(py_trees.display.ascii_tree(root))

    # 실행
    print("\n실행 시작:")
    while root.status != py_trees.common.Status.SUCCESS and \
          root.status != py_trees.common.Status.FAILURE:
        tree.tick()
        time.sleep(0.1)

    print(f"\n결과: {root.status}")
    print("\n최종 트리 상태:")
    print(py_trees.display.ascii_tree(root, show_status=True))

    arm.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
