# Week 2: Behavior Tree (행동 트리)

## 개요

Week 1의 State Machine을 발전시킨 **Behavior Tree(행동 트리)**를 배웁니다.

## State Machine vs Behavior Tree

| | State Machine | Behavior Tree |
|--|--------------|---------------|
| 구조 | 선형 (A→B→C) | 트리 (가지치기) |
| 재사용 | 어려움 | 행동을 모듈처럼 조합 |
| 실패 처리 | 직접 코딩 | Fallback 노드로 자동 |
| 복잡도 | 상태 많으면 폭발 | 트리로 깔끔 관리 |

## Behavior Tree 기본 노드

```
Sequence (→): 순서대로 실행, 하나라도 실패하면 전체 실패
Fallback (?): 순서대로 시도, 하나 성공하면 전체 성공
Action  (□): 실제 행동 (이동, 잡기 등)
Condition (○): 조건 확인 (물체 있나? 잡았나?)
```

## Pick & Place를 Behavior Tree로:
```
        [Root: Sequence]
        ├── [Setup: Sequence]
        │   ├── □ Home 이동
        │   └── □ 그리퍼 열기
        ├── [Pick: Sequence]
        │   ├── □ 물체 위로 접근
        │   ├── □ 내려가기
        │   └── □ 잡기
        ├── [Place: Sequence]
        │   ├── □ 들어올리기
        │   ├── □ 목적지로 이동
        │   ├── □ 내려놓기
        │   └── □ 놓기
        └── □ Home 복귀
```

## 실습 구성

| 파일 | 내용 | 난이도 |
|------|------|--------|
| `01_bt_basics.py` | Behavior Tree 기초 이해 | ★ |
| `02_bt_pick_place.py` | BT로 pick & place 구현 | ★★ |
| `03_bt_mission.py` | Fallback + 재시도 로직 | ★★★ |

## 실행 방법
```bash
# 터미널 1
ros2 launch soarm101_pick_place gazebo_moveit.launch.py

# 터미널 2
cd ~/soarm101_ros2_moveit/projects/week2_behavior_tree
python3 01_bt_basics.py
```
