#!/usr/bin/env python3
"""02. State Machine으로 Pick & Place

상태 기계(State Machine) 패턴으로 물체를 잡아서 옮기는 로봇.

상태 다이어그램:
  INIT → APPROACH → DESCEND → GRASP → LIFT → TRANSPORT → LOWER → RELEASE → RETREAT → DONE

★ 과제:
  1. 코드를 실행하고 Gazebo에서 동작 확인
  2. CUBE_PICK, CUBE_PLACE 값을 수정해서 다른 위치로 옮겨보기
  3. 실패 처리 추가: 이동 실패 시 HOME으로 돌아가기
"""

import time
import rclpy
from robot_arm import RobotArm


# ============================================================
# ★ 수정 가능한 설정값
# ============================================================

# 큐브 잡는 위치 (조인트 각도, radian)
CUBE_PICK = {
    "above": dict(shoulder_pan=0.0, shoulder_lift=1.0, elbow_flex=-0.9,
                  wrist_flex=-1.1, wrist_roll=0.0),
    "down":  dict(shoulder_pan=0.0, shoulder_lift=1.35, elbow_flex=-1.15,
                  wrist_flex=-1.3, wrist_roll=0.0),
}

# 큐브 놓는 위치
CUBE_PLACE = {
    "above": dict(shoulder_pan=1.3, shoulder_lift=1.0, elbow_flex=-0.9,
                  wrist_flex=-1.1, wrist_roll=0.0),
    "down":  dict(shoulder_pan=1.3, shoulder_lift=1.35, elbow_flex=-1.15,
                  wrist_flex=-1.3, wrist_roll=0.0),
}


# ============================================================
# State Machine 구현
# ============================================================

class PickPlaceStateMachine:
    """Pick & Place 상태 기계

    States:
        INIT      → 초기화 (홈 위치, 그리퍼 열기)
        APPROACH  → 물체 위로 이동
        DESCEND   → 물체 높이로 내려가기
        GRASP     → 그리퍼 닫기 (잡기)
        LIFT      → 들어올리기
        TRANSPORT → 목적지 위로 이동
        LOWER     → 목적지 높이로 내려가기
        RELEASE   → 그리퍼 열기 (놓기)
        RETREAT   → 위로 올라가기
        DONE      → 완료
        ERROR     → 오류 발생
    """

    def __init__(self, arm):
        self.arm = arm
        self.state = "INIT"
        self.history = []  # 상태 전환 기록

    def run(self):
        """상태 기계 실행 — 완료될 때까지 반복"""
        print(f"\n{'='*50}")
        print(f"  State Machine 시작")
        print(f"{'='*50}\n")

        while self.state != "DONE" and self.state != "ERROR":
            self._transition()
            time.sleep(0.3)

        print(f"\n{'='*50}")
        print(f"  결과: {self.state}")
        print(f"  상태 전환 기록: {' → '.join(self.history)}")
        print(f"{'='*50}\n")

    def _transition(self):
        """현재 상태에 따라 행동 수행 + 다음 상태 결정"""
        old_state = self.state
        self.history.append(self.state)
        print(f"  [{self.state}]", end=" ")

        # ─── 각 상태별 행동 ─────────────
        if self.state == "INIT":
            self.arm.gripper_open()
            ok = self.arm.home()
            self.state = "APPROACH" if ok else "ERROR"

        elif self.state == "APPROACH":
            print("물체 위로 이동")
            ok = self.arm.move_joints(**CUBE_PICK["above"])
            self.state = "DESCEND" if ok else "ERROR"

        elif self.state == "DESCEND":
            print("내려가기")
            ok = self.arm.move_joints(**CUBE_PICK["down"])
            self.state = "GRASP" if ok else "ERROR"

        elif self.state == "GRASP":
            print("잡기!")
            self.arm.gripper_close()
            time.sleep(0.5)
            self.state = "LIFT"

        elif self.state == "LIFT":
            print("들어올리기")
            ok = self.arm.move_joints(**CUBE_PICK["above"])
            self.state = "TRANSPORT" if ok else "ERROR"

        elif self.state == "TRANSPORT":
            print("목적지로 이동")
            ok = self.arm.move_joints(**CUBE_PLACE["above"])
            self.state = "LOWER" if ok else "ERROR"

        elif self.state == "LOWER":
            print("내려놓기 위치로")
            ok = self.arm.move_joints(**CUBE_PLACE["down"])
            self.state = "RELEASE" if ok else "ERROR"

        elif self.state == "RELEASE":
            print("놓기!")
            self.arm.gripper_open()
            time.sleep(0.3)
            self.state = "RETREAT"

        elif self.state == "RETREAT":
            print("후퇴")
            ok = self.arm.move_joints(**CUBE_PLACE["above"])
            self.state = "DONE" if ok else "ERROR"

        elif self.state == "ERROR":
            print("오류! 홈으로 복귀")
            self.arm.home()

        if self.state != old_state:
            print(f"    → {self.state}")


# ============================================================
# 메인
# ============================================================

def main():
    rclpy.init()
    arm = RobotArm()

    # Gazebo에 큐브 배치
    print("Gazebo에 물체 배치 중...")
    arm.spawn_table()
    time.sleep(0.3)
    arm.spawn_box("red_cube", 0.12, 0.0, 0.025, size=0.03, r=1, g=0, b=0)
    arm.spawn_zone("target_zone", 0.05, 0.18, 1, 0.3, 0.3)
    time.sleep(1)

    # State Machine 실행
    sm = PickPlaceStateMachine(arm)
    sm.run()

    # 홈 복귀
    arm.home()

    arm.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
