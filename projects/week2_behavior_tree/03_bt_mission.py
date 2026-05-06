#!/usr/bin/env python3
"""03. Behavior Tree 확장: Fallback + 재시도

BT의 핵심 장점인 Fallback(실패 시 대안)과 Retry(재시도)를 구현합니다.

트리 구조:
    [Root: Sequence]
    ├── Setup
    └── [ForEachCube: Sequence]
        └── [PickPlace with Retry]
            ├── [Try: Sequence] ← 1차 시도
            │   ├── Pick
            │   └── Place
            └── [Fallback: Sequence] ← 실패 시
                ├── Home 복귀
                └── [Retry: Sequence] ← 2차 시도
                    ├── Pick
                    └── Place

★ 과제:
  1. 실행해서 동작 확인
  2. 일부러 실패하는 상황 만들기 (조인트 범위 밖 값)
  3. Fallback이 작동하는지 확인
  4. 3개 큐브 분류로 확장
"""

import time
import py_trees
import rclpy
from robot_arm import RobotArm


# ─── 행동 노드 (02에서 재사용) ───────────────

class MoveJoints(py_trees.behaviour.Behaviour):
    def __init__(self, name, arm, **joints):
        super().__init__(name)
        self.arm = arm
        self.joints = joints

    def update(self):
        print(f"    → {self.name}")
        ok = self.arm.move_joints(**self.joints)
        return py_trees.common.Status.SUCCESS if ok else py_trees.common.Status.FAILURE


class GripperAction(py_trees.behaviour.Behaviour):
    def __init__(self, name, arm, open=True):
        super().__init__(name)
        self.arm = arm
        self.open = open

    def update(self):
        self.arm.gripper_open() if self.open else self.arm.gripper_close()
        time.sleep(0.3)
        print(f"    → {self.name}")
        return py_trees.common.Status.SUCCESS


class LogAction(py_trees.behaviour.Behaviour):
    """로그 메시지 출력"""
    def __init__(self, name, message):
        super().__init__(name)
        self.message = message

    def update(self):
        print(f"\n  ★ {self.message}")
        return py_trees.common.Status.SUCCESS


# ─── 포즈 ────────────────────────────────

CUBES = [
    {
        "name": "red",
        "spawn": {"x": 0.12, "y": 0.0, "z": 0.025, "r": 1, "g": 0, "b": 0},
        "pick_above": dict(shoulder_pan=0.0, shoulder_lift=1.0, elbow_flex=-0.9,
                           wrist_flex=-1.1, wrist_roll=0.0),
        "pick_down": dict(shoulder_pan=0.0, shoulder_lift=1.35, elbow_flex=-1.15,
                          wrist_flex=-1.3, wrist_roll=0.0),
        "place_above": dict(shoulder_pan=1.3, shoulder_lift=1.0, elbow_flex=-0.9,
                            wrist_flex=-1.1, wrist_roll=0.0),
        "place_down": dict(shoulder_pan=1.3, shoulder_lift=1.35, elbow_flex=-1.15,
                           wrist_flex=-1.3, wrist_roll=0.0),
    },
]

HOME = dict(shoulder_pan=0.0, shoulder_lift=-0.5, elbow_flex=1.0,
            wrist_flex=-0.5, wrist_roll=0.0)


# ─── 트리 구성 ───────────────────────────

def make_pick_subtree(arm, cube, attempt=""):
    """Pick 서브트리"""
    label = f"{cube['name']}{attempt}"
    pick = py_trees.composites.Sequence(f"Pick_{label}", memory=True)
    pick.add_children([
        GripperAction(f"Open_{label}", arm, open=True),
        MoveJoints(f"Approach_{label}", arm, **cube["pick_above"]),
        MoveJoints(f"Descend_{label}", arm, **cube["pick_down"]),
        GripperAction(f"Grasp_{label}", arm, open=False),
    ])
    return pick


def make_place_subtree(arm, cube, attempt=""):
    """Place 서브트리"""
    label = f"{cube['name']}{attempt}"
    place = py_trees.composites.Sequence(f"Place_{label}", memory=True)
    place.add_children([
        MoveJoints(f"Lift_{label}", arm, **cube["pick_above"]),
        MoveJoints(f"Transport_{label}", arm, **cube["place_above"]),
        MoveJoints(f"Lower_{label}", arm, **cube["place_down"]),
        GripperAction(f"Release_{label}", arm, open=True),
        MoveJoints(f"Retreat_{label}", arm, **cube["place_above"]),
    ])
    return place


def create_mission_tree(arm):
    """미션 트리 생성 — Fallback으로 재시도 포함"""

    root = py_trees.composites.Sequence("Mission", memory=True)

    # Setup
    setup = py_trees.composites.Sequence("Setup", memory=True)
    setup.add_children([
        LogAction("시작", "미션 시작!"),
        MoveJoints("Home", arm, **HOME),
    ])
    root.add_child(setup)

    # 각 큐브에 대해 Pick & Place with Fallback
    for cube in CUBES:
        # 1차 시도
        first_try = py_trees.composites.Sequence(f"Try_{cube['name']}", memory=True)
        first_try.add_children([
            LogAction(f"1차시도_{cube['name']}", f"{cube['name']} 큐브 1차 시도"),
            make_pick_subtree(arm, cube),
            make_place_subtree(arm, cube),
        ])

        # 2차 시도 (1차 실패 시)
        retry = py_trees.composites.Sequence(f"Retry_{cube['name']}", memory=True)
        retry.add_children([
            LogAction(f"재시도_{cube['name']}", f"{cube['name']} 큐브 재시도!"),
            MoveJoints(f"Home_retry_{cube['name']}", arm, **HOME),
            make_pick_subtree(arm, cube, "_retry"),
            make_place_subtree(arm, cube, "_retry"),
        ])

        # Fallback: 1차 시도 → 실패 시 재시도
        with_retry = py_trees.composites.Selector(
            f"WithRetry_{cube['name']}", memory=True
        )
        with_retry.add_children([first_try, retry])

        root.add_child(with_retry)

    # 마무리
    root.add_child(MoveJoints("Home_final", arm, **HOME))
    root.add_child(LogAction("완료", "미션 완료!"))

    return root


# ─── 메인 ────────────────────────────────

def main():
    rclpy.init()
    arm = RobotArm()

    print("=" * 50)
    print("  Behavior Tree: 미션 (Fallback + 재시도)")
    print("=" * 50)

    # 환경 배치
    arm.spawn_table()
    time.sleep(0.3)
    for cube in CUBES:
        s = cube["spawn"]
        arm.spawn_box(f"{cube['name']}_cube", s["x"], s["y"], s["z"],
                      r=s["r"], g=s["g"], b=s["b"])
        arm.spawn_zone(f"zone_{cube['name']}", 0.05, 0.18, s["r"], s["g"]*0.3, s["b"]*0.3)
    time.sleep(1)

    # 트리 생성 & 출력
    root = create_mission_tree(arm)
    tree = py_trees.trees.BehaviourTree(root)

    print("\n트리 구조:")
    print(py_trees.display.ascii_tree(root))

    # 실행
    print("\n" + "-" * 50)
    print("  실행 시작")
    print("-" * 50)

    while root.status != py_trees.common.Status.SUCCESS and \
          root.status != py_trees.common.Status.FAILURE:
        tree.tick()
        time.sleep(0.1)

    print(f"\n결과: {root.status}")

    arm.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
