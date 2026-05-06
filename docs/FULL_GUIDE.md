# SO-ARM101 + ROS2 + MoveIt2 + Gazebo 전체 가이드

> 작성일: 2026-05-05
> 환경: Ubuntu 24.04 LTS, ROS2 Jazzy, Gazebo Harmonic

---

## 목차

1. [배경 지식](#1-배경-지식)
2. [설치](#2-설치)
3. [프로젝트 구조](#3-프로젝트-구조)
4. [실행 방법](#4-실행-방법)
5. [해볼 수 있는 것들](#5-해볼-수-있는-것들)
6. [교육용 프로젝트](#6-교육용-프로젝트)
7. [트러블슈팅](#7-트러블슈팅)
8. [참고 자료](#8-참고-자료)

---

## 1. 배경 지식

### 1.1 ROS2 (Robot Operating System 2)

- **만든 곳**: Open Robotics (현재 Intrinsic, Google X 산하)
- **역할**: 로봇 소프트웨어 개발을 위한 **표준 프레임워크**
- **보편성**: 산업/학계에서 사실상 표준. Boston Dynamics, NASA, Amazon Robotics, 현대로보틱스 등 사용
- **핵심 개념**:
  - **Node**: 하나의 기능 단위 (예: 카메라 노드, 모터 노드)
  - **Topic**: 노드 간 데이터 전달 통로 (발행/구독 방식)
  - **Service**: 요청-응답 방식 통신
  - **Action**: 장시간 작업 (예: "5초 동안 이동" → 진행률 피드백)
  - **Launch**: 여러 노드를 한 번에 실행하는 스크립트

```
[카메라 노드] --/image 토픽--> [감지 노드] --/object_pose 토픽--> [제어 노드]
```

- **버전**: ROS2 Jazzy Jalisco (2024.05, Ubuntu 24.04용, 2029년까지 지원)
- **이전 버전과 차이**: ROS1은 단일 마스터 구조, ROS2는 DDS 기반 분산 구조

### 1.2 MoveIt2

- **만든 곳**: PickNik Robotics (오픈소스)
- **역할**: 로봇 팔의 **모션 플래닝** 프레임워크
- **보편성**: ROS 생태계에서 매니퓰레이터 제어의 **사실상 표준**. UR, Franka, KUKA 등 대부분의 산업용 로봇 팔이 MoveIt을 지원
- **핵심 기능**:

| 기능 | 설명 |
|------|------|
| **Motion Planning** | 시작점→목표점 충돌 없는 경로 생성 |
| **Collision Detection** | 로봇이 자기 자신이나 환경과 부딪히는지 검사 |
| **Inverse Kinematics (IK)** | "이 위치에 손 갖다 놓아" → 각 관절 각도 계산 |
| **Cartesian Path** | 직선/곡선 경로를 따라 end-effector 이동 |
| **Grasp Planning** | 물체를 잡는 최적 자세 계산 |

- **플래너 종류**:
  - **OMPL** (Open Motion Planning Library): 샘플링 기반 (RRT, PRM 등). 기본 플래너
  - **CHOMP**: 최적화 기반, 부드러운 경로
  - **STOMP**: 확률적 최적화, 장애물 회피에 강함
  - **Pilz**: 산업용, PTP/LIN/CIRC 등 단순 동작

- **구성 요소**:

```
┌──────────────────────────────────────────┐
│               MoveIt2                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │  OMPL    │ │  KDL     │ │ Planning │ │
│  │ Planner  │ │ IK Solver│ │  Scene   │ │
│  └──────────┘ └──────────┘ └──────────┘ │
├──────────────────────────────────────────┤
│           ros2_control                    │
│  ┌──────────────────────────────────┐    │
│  │  joint_trajectory_controller     │    │
│  │  joint_state_broadcaster         │    │
│  │  gripper_controller              │    │
│  └──────────────────────────────────┘    │
├──────────────────────────────────────────┤
│          Hardware Interface              │
│  mock_components │ real (Feetech) │ Gazebo│
└──────────────────────────────────────────┘
```

### 1.3 Gazebo

- **만든 곳**: Open Robotics (ROS와 같은 조직)
- **역할**: 3D **물리 시뮬레이터** (중력, 충돌, 마찰 등)
- **보편성**: ROS 생태계의 표준 시뮬레이터. DARPA Robotics Challenge에서 사용
- **현재 버전**: Gazebo Harmonic (gz-sim 8.x). 과거 "Gazebo Classic"과 구분
- **물리 엔진**: Bullet (기본), DART, ODE 지원
- **핵심 기능**:
  - 로봇을 가상 환경에서 테스트 (실제 로봇 없이)
  - 중력, 마찰, 충돌 시뮬레이션
  - 가상 카메라, LIDAR 등 센서 시뮬레이션
  - 여러 로봇 동시 시뮬레이션

### 1.4 ros2_control

- **역할**: ROS2에서 **로봇 하드웨어를 추상화**하는 프레임워크
- **핵심**: 같은 코드로 시뮬레이션/실제 하드웨어를 전환 가능

```
              동일한 MoveIt 코드
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
  mock_components   real      gazebo
  (가짜, 즉시응답) (USB 서보) (물리 시뮬)
```

- `hardware_type` 파라미터 하나로 전환:
  - `mock_components`: 하드웨어 없이 RViz에서만 동작
  - `real`: 실제 서보 모터 (Feetech STS3215)
  - `gazebo`: Gazebo 물리 시뮬레이션

### 1.5 URDF / SRDF

- **URDF** (Unified Robot Description Format): 로봇의 **물리적 구조** 정의
  - 링크 (뼈대), 조인트 (관절), 메시 (3D 모양), 질량, 관성
  - XML 형식

- **SRDF** (Semantic Robot Description Format): MoveIt용 **의미적 정보**
  - 조인트 그룹 (예: "manipulator" = 어깨~손목, "gripper" = 그리퍼)
  - 명명된 자세 (예: "home", "extended", "rest")
  - 충돌 제외 쌍 (인접 링크 간 충돌 무시)

### 1.6 SO-ARM101

- **만든 곳**: TheRobotStudio / Hugging Face LeRobot 프로젝트
- **특징**: 저비용 3D프린팅 6-DOF 로봇팔, 교육/연구용
- **서보**: Feetech STS3215 × 6 (시리얼 버스 통신, 1Mbps)
- **자유도**: 5 arm joints + 1 gripper

| 조인트 | 서보 ID | 기능 | 범위 |
|--------|---------|------|------|
| shoulder_pan | 1 | base 회전 | ±110° |
| shoulder_lift | 2 | 어깨 | ±100° |
| elbow_flex | 3 | 팔꿈치 | -97°~88° |
| wrist_flex | 4 | 손목 굽힘 | ±92° |
| wrist_roll | 5 | 손목 회전 | ±132° |
| gripper | 6 | 그리퍼 | 0°~97° |

### 1.7 로봇 제어 패러다임 발전

| 세대 | 방식 | 특징 | 대표 기술 |
|------|------|------|----------|
| 1세대 | **State Machine** | 상태와 전환을 명시적 정의 | FSM, 하드코딩 |
| 2세대 | **Behavior Tree** | 트리 구조로 행동 조합, 재사용 가능 | py_trees, BT.CPP |
| 3세대 | **학습 기반** | 데이터로부터 행동 학습 | RL, 모방학습 (LeRobot) |

---

## 2. 설치

### 2.1 ROS2 Jazzy 설치

```bash
# 1. locale 설정
sudo apt update && sudo apt install -y locales software-properties-common curl
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

# 2. ROS2 GPG key + repository
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# 3. 설치
sudo apt update
sudo apt install -y ros-jazzy-desktop ros-dev-tools

# 4. 환경 자동 로드
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source /opt/ros/jazzy/setup.bash
```

> **참고**: Ubuntu 미러가 느리면 `kr.archive.ubuntu.com`으로 변경
> ```bash
> sudo sed -i 's|archive.ubuntu.com|kr.archive.ubuntu.com|g' /etc/apt/sources.list.d/ubuntu.sources
> ```

### 2.2 MoveIt2 설치

```bash
sudo apt install -y ros-jazzy-moveit
```

### 2.3 Gazebo 설치

```bash
sudo apt install -y ros-jazzy-gz-ros2-control ros-jazzy-ros-gz ros-jazzy-gz-sim-vendor
```

### 2.4 추가 패키지

```bash
sudo apt install -y \
  ros-jazzy-nav2-common \
  ros-jazzy-hardware-interface \
  ros-jazzy-controller-manager \
  ros-jazzy-joint-state-broadcaster \
  ros-jazzy-joint-trajectory-controller \
  ros-jazzy-position-controllers \
  ros-jazzy-parallel-gripper-controller \
  ros-jazzy-ros2controlcli \
  ros-jazzy-xacro \
  ros-jazzy-foxglove-bridge \
  librange-v3-dev \
  libserial-dev

# Behavior Tree 라이브러리
pip3 install --break-system-packages py_trees
```

### 2.5 SO-ARM101 워크스페이스 구성

```bash
mkdir -p ~/soarm101_ros2_moveit/ws/src
cd ~/soarm101_ros2_moveit/ws/src

# 핵심 패키지 클론
git clone https://github.com/JafarAbdi/ros2_so_arm100.git    # URDF + MoveIt + Gazebo
git clone https://github.com/JafarAbdi/feetech_ros2_driver.git  # STS3215 서보 드라이버

# rosdep 초기화 + 의존성 설치
cd ~/soarm101_ros2_moveit/ws
sudo rosdep init  # 최초 1회
rosdep update
rosdep install --from-paths src --ignore-src -r -y

# 빌드
colcon build --symlink-install
source install/setup.bash

# bashrc에 추가
echo "source ~/soarm101_ros2_moveit/ws/install/setup.bash" >> ~/.bashrc
```

### 2.6 출처 정리

| 패키지 | 출처 | 설명 |
|--------|------|------|
| `ros2_so_arm100` | [JafarAbdi/ros2_so_arm100](https://github.com/JafarAbdi/ros2_so_arm100) | SO-ARM100/101 URDF, MoveIt config, Gazebo |
| `feetech_ros2_driver` | [JafarAbdi/feetech_ros2_driver](https://github.com/JafarAbdi/feetech_ros2_driver) | Feetech STS3215 ros2_control 플러그인 |
| `so_arm101_moveit_config` | **우리가 생성** | SO-ARM101용 MoveIt config (원본 repo에 없음) |
| `soarm101_pick_place` | **우리가 생성** | Gazebo+MoveIt 통합 launch, pick&place 노드 |

---

## 3. 프로젝트 구조

```
~/soarm101_ros2_moveit/
├── README.md
├── docs/
│   ├── 01_setup_guide.md           # 설치 가이드
│   ├── 02_package_structure.md     # 아키텍처
│   ├── 03_troubleshooting.md       # 트러블슈팅
│   ├── 04_quick_commands.md        # 명령어 모음
│   ├── 05_pick_place_project.md    # ArUco Pick & Place
│   └── FULL_GUIDE.md              # 이 문서
│
├── examples/                       # Gazebo 예제
│   ├── gz_01_named_poses.py        # 자세 이동
│   ├── gz_02_collision_scene.py    # 충돌 회피
│   ├── gz_03_pick_place_sim.py     # Pick & Place
│   ├── gz_04_waypoints.py          # 패턴 그리기
│   └── gz_05_digital_twin.py       # 디지털 트윈 (실험적)
│
├── projects/                       # 교육용 프로젝트
│   ├── week1_state_machine/        # Week 1: 상태 기계
│   │   ├── README.md
│   │   ├── robot_arm.py            # 공통 라이브러리
│   │   ├── 01_hello_robot.py       # 기본 제어
│   │   ├── 02_state_machine.py     # SM pick & place
│   │   └── 03_mission.py           # 다중 물체 분류
│   └── week2_behavior_tree/        # Week 2: 행동 트리
│       ├── README.md
│       ├── robot_arm.py
│       ├── 01_bt_basics.py         # BT 개념
│       ├── 02_bt_pick_place.py     # BT pick & place
│       └── 03_bt_mission.py        # Fallback + 재시도
│
├── tools/
│   └── generate_aruco_markers.py   # ArUco 마커 생성
│
└── ws/                             # ROS2 워크스페이스
    └── src/
        ├── ros2_so_arm100/         # (git clone)
        │   ├── so_arm100_description/
        │   ├── so_arm100_moveit_config/
        │   ├── so_arm101_description/    # 6-DOF URDF + 메시
        │   ├── so_arm101_moveit_config/  # ← 우리가 생성
        │   ├── so_arm_gz/                # Gazebo launch
        │   └── so_arm_utils/             # launch 유틸리티
        ├── feetech_ros2_driver/    # (git clone)
        └── soarm101_pick_place/    # ← 우리가 생성
            ├── config/             # 카메라 캘리브레이션, SDF 월드
            ├── launch/             # gazebo_moveit, digital_twin 등
            └── soarm101_pick_place/  # Python 노드들
```

---

## 4. 실행 방법

### 4.1 기본 실행 (매번 필요)

```bash
# 모든 터미널에서
source /opt/ros/jazzy/setup.bash
source ~/soarm101_ros2_moveit/ws/install/setup.bash
```

### 4.2 MoveIt Demo (mock, 하드웨어 불필요)

```bash
ros2 launch so_arm101_moveit_config demo.launch.py hardware_type:=mock_components
```
- RViz에서 로봇을 드래그하고 "Plan & Execute"로 모션 플래닝 체험
- 물리 시뮬레이션 없음, MoveIt 인터페이스만 확인

### 4.3 Gazebo + MoveIt (물리 시뮬레이션)

```bash
# 터미널 1: 시뮬레이션
ros2 launch soarm101_pick_place gazebo_moveit.launch.py

# Gazebo 카메라 시점 조정 (로봇이 안 보이면)
gz service -s /gui/move_to/pose \
  --reqtype gz.msgs.GUICamera --reptype gz.msgs.Boolean --timeout 3000 \
  --req "pose: {position: {x: 1.0, y: 0.0, z: 1.0}, orientation: {x: -0.27, y: 0.27, z: 0.65, w: 0.65}}"

# 터미널 2: 예제 실행
python3 ~/soarm101_ros2_moveit/examples/gz_01_named_poses.py
```

### 4.4 실제 하드웨어

```bash
# USB 권한 설정
sudo chmod 666 /dev/ttyACM0

# 실행
ros2 launch so_arm101_moveit_config demo.launch.py hardware_type:=real usb_port:=/dev/ttyACM0
```

### 4.5 유용한 명령어

```bash
# 토픽 확인
ros2 topic list
ros2 topic echo /joint_states

# 컨트롤러 확인
ros2 control list_controllers
ros2 control list_hardware_interfaces

# TF 트리 시각화
ros2 run tf2_tools view_frames

# Gazebo 모델 목록
gz model --list
```

---

## 5. 해볼 수 있는 것들

### 5.1 Gazebo 예제 (검증 완료)

| 예제 | 파일 | 내용 |
|------|------|------|
| Named Poses | `gz_01_named_poses.py` | zero→extended→rest→zero 이동 |
| Collision Scene | `gz_02_collision_scene.py` | 장애물 배치 + 충돌 회피 경로 |
| Pick & Place | `gz_03_pick_place_sim.py` | 큐브 스폰 + 잡기 시퀀스 |
| Waypoints | `gz_04_waypoints.py` | 사각형/원형 패턴 |

### 5.2 교육용 프로젝트

| 주차 | 주제 | 핵심 파일 |
|------|------|----------|
| Week 1 | State Machine | `02_state_machine.py` (검증 완료) |
| Week 2 | Behavior Tree | `02_bt_pick_place.py` |

### 5.3 향후 가능한 프로젝트

| 프로젝트 | 난이도 | 설명 |
|----------|--------|------|
| MoveIt Task Constructor | 중 | 스테이지 기반 복합 작업 |
| 가상 카메라 + 물체 인식 | 중 | Gazebo 카메라 → OpenCV → MoveIt |
| 멀티암 협동 | 중 | Gazebo에 2대 배치 |
| LeRobot + ROS2 | 중상 | 모방학습 → ROS2 배포 |
| 플래너 벤치마크 | 중 | OMPL vs CHOMP vs STOMP 비교 |
| Foxglove 대시보드 | 쉬움 | 웹 브라우저에서 모니터링 |

---

## 6. 교육용 프로젝트

### 6.1 대상

- 학부 비전공자
- 기간: 2주
- 사전 지식: Python 기초

### 6.2 Week 1: State Machine

**개념**: 상태(State)와 전환(Transition)으로 로봇 동작 정의

```
[INIT] → [APPROACH] → [DESCEND] → [GRASP] → [LIFT] → [TRANSPORT] → [LOWER] → [RELEASE] → [DONE]
```

**실습 흐름**:
1. `01_hello_robot.py`: 로봇 이동, 그리퍼 열기/닫기 체험
2. `02_state_machine.py`: State Machine으로 pick & place 실행
3. `03_mission.py`: 3개 큐브를 색상별로 분류 (과제)

**학생이 수정하는 부분**: 조인트 각도, 분류 순서, 장애물 추가

### 6.3 Week 2: Behavior Tree

**개념**: 트리 구조로 행동을 모듈화, Fallback으로 실패 자동 처리

```
      [Root: Sequence]
      ├── [Setup]
      ├── [Pick: Sequence]
      │   ├── Approach
      │   ├── Descend
      │   └── Grasp
      ├── [Place: Sequence]
      │   ├── Lift
      │   ├── Transport
      │   └── Release
      └── Home
```

**실습 흐름**:
1. `01_bt_basics.py`: py_trees 개념 (로봇 없이)
2. `02_bt_pick_place.py`: BT로 pick & place
3. `03_bt_mission.py`: Fallback + 재시도 로직

**State Machine과 비교할 점**:
- SM: 상태 10개 → 전환 조건 10개 → 복잡해지면 관리 어려움
- BT: 행동 모듈 조합 → Sequence/Fallback으로 구조화 → 재사용 가능

---

## 7. 트러블슈팅

### 빌드 에러

```bash
# rosdep 안 된 경우
sudo rosdep init && rosdep update

# range-v3 못 찾을 때
sudo apt install -y librange-v3-dev libserial-dev

# 특정 패키지만 재빌드
colcon build --symlink-install --packages-select so_arm101_moveit_config
```

### Gazebo 관련

```bash
# Gazebo 카메라 시점이 로봇에서 멀 때
gz service -s /gui/move_to/pose --reqtype gz.msgs.GUICamera --reptype gz.msgs.Boolean --timeout 3000 \
  --req "pose: {position: {x: 1.0, y: 0.0, z: 1.0}, orientation: {x: -0.27, y: 0.27, z: 0.65, w: 0.65}}"

# gz 명령 못 찾을 때
source /opt/ros/jazzy/setup.bash  # 반드시 source 후 사용

# demo.launch.py hardware_type:=gazebo는 안 됨
# → gazebo_moveit.launch.py 사용
```

### 실제 하드웨어

```bash
# USB 권한
sudo chmod 666 /dev/ttyACM0
# 또는 영구 설정
sudo usermod -aG dialout $USER  # 재로그인 필요

# 포트 사용 중
sudo fuser -k /dev/ttyACM0

# feetech 드라이버가 sudo 필요할 때 → chmod 666으로 해결
```

### 프로세스 정리

```bash
# 모든 ROS/Gazebo 프로세스 종료
pkill -9 -f "gz|rviz|move_group|ros2_control|robot_state|parameter_bridge|spawner"
```

---

## 8. 참고 자료

### 공식 문서

| 자료 | URL |
|------|-----|
| ROS2 Jazzy 문서 | https://docs.ros.org/en/jazzy/ |
| MoveIt2 문서 | https://moveit.picknik.ai/main/ |
| Gazebo 문서 | https://gazebosim.org/docs/harmonic/ |
| ros2_control 문서 | https://control.ros.org/ |

### SO-ARM101 관련

| 자료 | URL |
|------|-----|
| SO-ARM100 공식 리포 | https://github.com/TheRobotStudio/SO-ARM100 |
| ros2_so_arm100 | https://github.com/JafarAbdi/ros2_so_arm100 |
| feetech_ros2_driver | https://github.com/JafarAbdi/feetech_ros2_driver |
| lerobot-ros (LeRobot↔ROS2) | https://github.com/ycheng517/lerobot-ros |
| SO-ARM101 Full-Stack 블로그 | https://thanhndv212.github.io/blog/2025/05/14/soarm/ |

### 교육 관련

| 자료 | 설명 |
|------|------|
| py_trees | https://py-trees.readthedocs.io/ |
| AutomaticAddison Jazzy 튜토리얼 | https://automaticaddison.com/tutorials/ |
| MoveIt Task Constructor | https://moveit.picknik.ai/main/doc/tutorials/pick_and_place_with_moveit_task_constructor/ |
