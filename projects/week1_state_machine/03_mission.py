#!/usr/bin/env python3
"""03. 확장 과제: 다중 물체 분류

State Machine을 확장하여 3개 큐브를 색상별로 분류합니다.

★ 과제:
  1. 3개 큐브(빨/파/초)를 각각 지정된 영역으로 분류
  2. 분류 순서를 바꿔보기
  3. 장애물을 추가하고 회피 경로로 분류 (add_collision_box 사용)
  4. 분류 결과를 출력하는 로그 추가
"""

import time
import rclpy
from robot_arm import RobotArm


# ============================================================
# ★ 학생이 채워야 하는 부분
# ============================================================

# 각 큐브의 Gazebo 스폰 위치 (x, y, z, 색상)
CUBES = {
    "red":   {"x": 0.12, "y":  0.00, "z": 0.025, "r": 1.0, "g": 0.0, "b": 0.0},
    "blue":  {"x": 0.18, "y":  0.05, "z": 0.025, "r": 0.0, "g": 0.0, "b": 1.0},
    "green": {"x": 0.15, "y": -0.05, "z": 0.025, "r": 0.0, "g": 0.8, "b": 0.0},
}

# 분류 영역 위치
ZONES = {
    "red":   {"x": 0.05, "y": 0.18},
    "blue":  {"x": 0.15, "y": 0.18},
    "green": {"x": 0.25, "y": 0.18},
}

# 각 큐브의 pick/place 조인트 각도
# ★ 힌트: 02_state_machine.py의 CUBE_PICK을 참고하여 채우세요!
PICK_POSES = {
    "red": {
        "above": dict(shoulder_pan=0.0, shoulder_lift=1.0, elbow_flex=-0.9,
                      wrist_flex=-1.1, wrist_roll=0.0),
        "down":  dict(shoulder_pan=0.0, shoulder_lift=1.35, elbow_flex=-1.15,
                      wrist_flex=-1.3, wrist_roll=0.0),
    },
    "blue": {
        # ★ 여기를 채우세요! blue 큐브는 (0.18, 0.05) 위치입니다.
        "above": dict(shoulder_pan=0.3, shoulder_lift=1.0, elbow_flex=-0.9,
                      wrist_flex=-1.1, wrist_roll=0.0),
        "down":  dict(shoulder_pan=0.3, shoulder_lift=1.35, elbow_flex=-1.15,
                      wrist_flex=-1.3, wrist_roll=0.0),
    },
    "green": {
        # ★ 여기를 채우세요! green 큐브는 (0.15, -0.05) 위치입니다.
        "above": dict(shoulder_pan=-0.3, shoulder_lift=1.0, elbow_flex=-0.9,
                      wrist_flex=-1.1, wrist_roll=0.0),
        "down":  dict(shoulder_pan=-0.3, shoulder_lift=1.35, elbow_flex=-1.15,
                      wrist_flex=-1.3, wrist_roll=0.0),
    },
}

PLACE_POSES = {
    "red": {
        "above": dict(shoulder_pan=1.4, shoulder_lift=0.8, elbow_flex=-0.8,
                      wrist_flex=-1.0, wrist_roll=0.0),
        "down":  dict(shoulder_pan=1.4, shoulder_lift=1.2, elbow_flex=-1.0,
                      wrist_flex=-1.2, wrist_roll=0.0),
    },
    "blue": {
        "above": dict(shoulder_pan=1.0, shoulder_lift=0.8, elbow_flex=-0.8,
                      wrist_flex=-1.0, wrist_roll=0.0),
        "down":  dict(shoulder_pan=1.0, shoulder_lift=1.2, elbow_flex=-1.0,
                      wrist_flex=-1.2, wrist_roll=0.0),
    },
    "green": {
        "above": dict(shoulder_pan=0.5, shoulder_lift=0.8, elbow_flex=-0.8,
                      wrist_flex=-1.0, wrist_roll=0.0),
        "down":  dict(shoulder_pan=0.5, shoulder_lift=1.2, elbow_flex=-1.0,
                      wrist_flex=-1.2, wrist_roll=0.0),
    },
}

# 분류 순서 — 바꿔보세요!
SORT_ORDER = ["red", "blue", "green"]


# ============================================================
# State Machine (02에서 확장)
# ============================================================

class SortingStateMachine:
    def __init__(self, arm, color, pick_poses, place_poses):
        self.arm = arm
        self.color = color
        self.pick = pick_poses
        self.place = place_poses
        self.state = "INIT"

    def run(self):
        states_order = [
            "INIT", "APPROACH", "DESCEND", "GRASP", "LIFT",
            "TRANSPORT", "LOWER", "RELEASE", "RETREAT", "DONE"
        ]

        while self.state != "DONE" and self.state != "ERROR":
            ok = True

            if self.state == "INIT":
                self.arm.gripper_open()
                ok = self.arm.home()

            elif self.state == "APPROACH":
                ok = self.arm.move_joints(**self.pick["above"])

            elif self.state == "DESCEND":
                ok = self.arm.move_joints(**self.pick["down"])

            elif self.state == "GRASP":
                self.arm.gripper_close()
                time.sleep(0.5)

            elif self.state == "LIFT":
                ok = self.arm.move_joints(**self.pick["above"])

            elif self.state == "TRANSPORT":
                ok = self.arm.move_joints(**self.place["above"])

            elif self.state == "LOWER":
                ok = self.arm.move_joints(**self.place["down"])

            elif self.state == "RELEASE":
                self.arm.gripper_open()
                time.sleep(0.3)

            elif self.state == "RETREAT":
                ok = self.arm.move_joints(**self.place["above"])

            # 다음 상태로 전환
            if not ok:
                print(f"    [{self.color}] {self.state} 실패!")
                self.state = "ERROR"
            else:
                idx = states_order.index(self.state)
                self.state = states_order[idx + 1]
                print(f"    [{self.color}] → {self.state}")

            time.sleep(0.2)

        return self.state == "DONE"


def main():
    rclpy.init()
    arm = RobotArm()

    print("=" * 50)
    print("  03. 다중 물체 분류 미션")
    print("=" * 50)

    # 환경 배치
    print("\n환경 배치 중...")
    arm.spawn_table()
    time.sleep(0.3)

    for color, info in CUBES.items():
        arm.spawn_box(f"{color}_cube", info["x"], info["y"], info["z"],
                      r=info["r"], g=info["g"], b=info["b"])
        time.sleep(0.3)

    for color, info in ZONES.items():
        arm.spawn_zone(f"zone_{color}", info["x"], info["y"],
                       *[CUBES[color][c] for c in "rgb"])
        time.sleep(0.2)

    time.sleep(1)

    # 분류 실행
    results = {}
    for i, color in enumerate(SORT_ORDER):
        print(f"\n--- [{i+1}/{len(SORT_ORDER)}] {color} 큐브 분류 ---")
        sm = SortingStateMachine(arm, color, PICK_POSES[color], PLACE_POSES[color])
        ok = sm.run()
        results[color] = "성공" if ok else "실패"

    # 결과 출력
    arm.home()
    print(f"\n{'='*50}")
    print("  분류 결과:")
    for color, result in results.items():
        print(f"    {color:6s}: {result}")
    print(f"{'='*50}\n")

    arm.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
