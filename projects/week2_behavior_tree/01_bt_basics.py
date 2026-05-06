#!/usr/bin/env python3
"""01. Behavior Tree 기초

py_trees 라이브러리로 간단한 Behavior Tree를 만들어봅니다.
로봇 없이 BT 개념만 먼저 이해합니다.

★ 과제: 맨 아래에 나만의 행동 트리를 만들어보세요
"""

import py_trees
import time


# ============================================================
# 커스텀 행동(Action) 정의
# ============================================================

class PrintAction(py_trees.behaviour.Behaviour):
    """메시지를 출력하는 행동"""
    def __init__(self, name, message):
        super().__init__(name)
        self.message = message

    def update(self):
        print(f"    실행: {self.message}")
        return py_trees.common.Status.SUCCESS


class WaitAction(py_trees.behaviour.Behaviour):
    """N번 tick해야 성공하는 행동 (시간이 걸리는 작업 시뮬)"""
    def __init__(self, name, ticks_to_complete=3):
        super().__init__(name)
        self.ticks_needed = ticks_to_complete
        self.tick_count = 0

    def update(self):
        self.tick_count += 1
        if self.tick_count >= self.ticks_needed:
            print(f"    완료: {self.name} ({self.tick_count} ticks)")
            return py_trees.common.Status.SUCCESS
        else:
            print(f"    진행중: {self.name} ({self.tick_count}/{self.ticks_needed})")
            return py_trees.common.Status.RUNNING


class FailAction(py_trees.behaviour.Behaviour):
    """항상 실패하는 행동"""
    def __init__(self, name):
        super().__init__(name)

    def update(self):
        print(f"    실패: {self.name}")
        return py_trees.common.Status.FAILURE


# ============================================================
# 예제 1: Sequence (순서 실행)
# ============================================================

def example_sequence():
    print("\n" + "=" * 50)
    print("  예제 1: Sequence (순서 실행)")
    print("  → 모든 행동이 성공해야 전체 성공")
    print("=" * 50)

    root = py_trees.composites.Sequence("아침 루틴", memory=True)
    root.add_children([
        PrintAction("알람끄기", "알람을 끕니다"),
        PrintAction("세수하기", "세수를 합니다"),
        PrintAction("아침먹기", "아침을 먹습니다"),
    ])

    tree = py_trees.trees.BehaviourTree(root)
    tree.tick()
    print(f"\n  결과: {root.status}")


# ============================================================
# 예제 2: Fallback (대안 실행)
# ============================================================

def example_fallback():
    print("\n" + "=" * 50)
    print("  예제 2: Fallback (대안 실행)")
    print("  → 하나 실패하면 다음 시도, 하나 성공하면 OK")
    print("=" * 50)

    root = py_trees.composites.Selector("이동수단 찾기", memory=True)
    root.add_children([
        FailAction("자동차"),       # 실패
        FailAction("자전거"),       # 실패
        PrintAction("걷기", "걸어갑니다"),  # 성공!
    ])

    tree = py_trees.trees.BehaviourTree(root)
    tree.tick()
    print(f"\n  결과: {root.status} (걷기로 성공!)")


# ============================================================
# 예제 3: 조합
# ============================================================

def example_combined():
    print("\n" + "=" * 50)
    print("  예제 3: Sequence + Fallback 조합")
    print("=" * 50)

    # 이동 방법 (Fallback)
    move = py_trees.composites.Selector("이동", memory=True)
    move.add_children([
        FailAction("택시"),
        PrintAction("버스", "버스를 탑니다"),
    ])

    # 전체 루틴 (Sequence)
    root = py_trees.composites.Sequence("출근", memory=True)
    root.add_children([
        PrintAction("준비", "출근 준비"),
        move,                              # 이동 (Fallback)
        PrintAction("도착", "회사 도착!"),
    ])

    tree = py_trees.trees.BehaviourTree(root)
    tree.tick()
    print(f"\n  결과: {root.status}")
    print(py_trees.display.ascii_tree(root))


# ============================================================

def main():
    print("=" * 50)
    print("  Behavior Tree 기초")
    print("=" * 50)

    example_sequence()
    example_fallback()
    example_combined()

    print("\n" + "=" * 50)
    print("  완료! 다음: python3 02_bt_pick_place.py")
    print("=" * 50)


if __name__ == "__main__":
    main()
