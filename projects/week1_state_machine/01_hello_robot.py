#!/usr/bin/env python3
"""01. 로봇 기본 제어 체험

로봇을 여러 자세로 이동시키고, 그리퍼를 열고 닫아봅니다.
Gazebo 화면에서 로봇이 움직이는 것을 확인하세요!

★ 과제: 맨 아래 my_pose() 함수에 자기만의 자세를 만들어보세요
"""

import time
import rclpy
from robot_arm import RobotArm


def main():
    rclpy.init()
    arm = RobotArm()

    print("=" * 50)
    print("  01. 로봇 기본 제어 체험")
    print("=" * 50)

    # ─── 기본 자세 ───────────────────
    print("\n[1] 홈 위치")
    arm.home()
    time.sleep(1)

    print("\n[2] 팔 뻗기")
    arm.move_joints(
        shoulder_pan=0.0,     # base 회전 안 함
        shoulder_lift=1.2,    # 어깨 들기
        elbow_flex=-1.0,      # 팔꿈치 펴기
        wrist_flex=-1.0,      # 손목
        wrist_roll=0.0,
    )
    time.sleep(1)

    # ─── 그리퍼 ──────────────────────
    print("\n[3] 그리퍼 열기")
    arm.gripper_open()
    time.sleep(0.5)

    print("\n[4] 그리퍼 닫기")
    arm.gripper_close()
    time.sleep(0.5)

    # ─── 회전 ────────────────────────
    print("\n[5] 왼쪽으로 회전")
    arm.move_joints(shoulder_pan=1.0, shoulder_lift=0.8,
                    elbow_flex=-0.8, wrist_flex=-0.8, wrist_roll=0.0)
    time.sleep(1)

    print("\n[6] 오른쪽으로 회전")
    arm.move_joints(shoulder_pan=-1.0, shoulder_lift=0.8,
                    elbow_flex=-0.8, wrist_flex=-0.8, wrist_roll=0.0)
    time.sleep(1)

    # ─── 홈 복귀 ─────────────────────
    print("\n[7] 홈 복귀")
    arm.home()

    # ─── 학생 과제 ───────────────────
    # ★ 아래 my_pose() 함수를 완성하세요!
    # print("\n[8] 나만의 자세")
    # my_pose(arm)

    print("\n" + "=" * 50)
    print("  완료! 다음: python3 02_state_machine.py")
    print("=" * 50)

    arm.destroy_node()
    rclpy.shutdown()


def my_pose(arm):
    """★ 과제: 자기만의 자세를 만들어보세요!

    각 조인트의 범위:
        shoulder_pan:  -1.92 ~ 1.92  (base 좌우 회전)
        shoulder_lift: -1.75 ~ 1.75  (어깨 위아래)
        elbow_flex:    -1.69 ~ 1.54  (팔꿈치)
        wrist_flex:    -1.60 ~ 1.60  (손목 굽힘)
        wrist_roll:    -2.30 ~ 2.30  (손목 회전)
    """
    arm.move_joints(
        shoulder_pan=0.0,
        shoulder_lift=0.0,
        elbow_flex=0.0,
        wrist_flex=0.0,
        wrist_roll=0.0,
    )


if __name__ == "__main__":
    main()
