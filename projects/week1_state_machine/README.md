# Week 1: State Machine (상태 기계) 로봇 제어

## 개요

로봇 제어의 가장 기본적인 방법인 **State Machine(상태 기계)**를 배웁니다.

상태 기계란?
```
상태(State)와 전환(Transition)으로 동작을 정의

  [대기] --물체발견--> [접근] --도착--> [잡기] --잡음--> [이동] --도착--> [놓기] --> [대기]
```

## 실습 구성

| 파일 | 내용 | 난이도 |
|------|------|--------|
| `01_hello_robot.py` | 로봇 기본 제어 (이동, 그리퍼) | ★ |
| `02_state_machine.py` | State Machine으로 pick & place | ★★ |
| `03_mission.py` | 확장 과제 (다중 물체 분류) | ★★★ |

## 실행 방법

```bash
# 터미널 1: 시뮬레이션 시작 (항상 먼저)
source /opt/ros/jazzy/setup.bash
source ~/soarm101_ros2_moveit/ws/install/setup.bash
ros2 launch soarm101_pick_place gazebo_moveit.launch.py

# 터미널 2: 예제 실행
cd ~/soarm101_ros2_moveit/projects/week1_state_machine
source /opt/ros/jazzy/setup.bash
source ~/soarm101_ros2_moveit/ws/install/setup.bash
python3 01_hello_robot.py
```

## State Machine이란?

```python
# 상태 정의
states = ["IDLE", "APPROACH", "GRASP", "LIFT", "TRANSPORT", "PLACE", "DONE"]

# 현재 상태
current_state = "IDLE"

# 전환 로직
while current_state != "DONE":
    if current_state == "IDLE":
        # 물체를 찾으면 → APPROACH
        current_state = "APPROACH"

    elif current_state == "APPROACH":
        # 물체 위로 이동 → GRASP
        robot.move_to(...)
        current_state = "GRASP"

    elif current_state == "GRASP":
        # 잡기 → LIFT
        robot.gripper_close()
        current_state = "LIFT"

    # ... 계속
```

## 핵심 개념

1. **State (상태)**: 로봇이 지금 뭘 하고 있는지
2. **Transition (전환)**: 다음 상태로 넘어가는 조건
3. **Action (행동)**: 각 상태에서 수행하는 동작
