# 00. ROS2 / MoveIt2 — 한 페이지로 잡는 멘탈 모델

이 문서는 **본 repo를 처음 만지는 사람**(강사 본인 + 학생)이
"ROS2 가 뭐고, ros2_control 이 뭐고, MoveIt2 가 어디 끼는지" 한 번에
잡기 위한 페이지입니다. 한 페이지 안에서 다 끝내는 게 목적이므로
깊이는 의도적으로 얕습니다.

---

## 1. ROS2 그림 한 장

```
   ┌──────────────────────────────────────────────────────┐
   │  하나의 컴퓨터 위에 "노드(Node)"가 여러 개 떠 있다.   │
   │                                                      │
   │   [노드 A] ── topic("/joint_states") ──▶ [노드 B]    │
   │   [노드 C] ── action("/move_group")  ──▶ [노드 D]    │
   │                                                      │
   │  노드끼리는 다음 셋 중 하나로 대화한다:               │
   │   • topic   — 단방향 스트림 (예: 센서 값)            │
   │   • service — 요청/응답 1회 (예: "현재 상태 줘")     │
   │   • action  — 오래 걸리는 요청 + 진행률 (예: 동작계획)│
   └──────────────────────────────────────────────────────┘
```

- **launch 파일** — "이 노드들 한꺼번에 켜라"는 레시피. 보통 `.launch.py`
- **워크스페이스(ws)** — 우리 코드를 모아 두는 폴더. `ws/src/` 안에
  패키지들이 들어있고, `colcon build` 가 그걸 `ws/build/`, `ws/install/`
  로 컴파일·설치
- **소스(sourcing)** — `source install/setup.bash` 를 해야 빌드한
  패키지를 `ros2 launch ...` 가 찾을 수 있다

```bash
cd ws && colcon build --symlink-install && source install/setup.bash
ros2 node list                    # 떠 있는 노드들
ros2 topic list                   # 발행 중인 토픽들
ros2 topic echo /joint_states     # 실시간 값 보기
```

---

## 2. ros2_control — "로봇 하드웨어와 ROS2 의 다리"

MoveIt 이 "이 시점에 어깨를 1.2 라디안으로 보내" 라는 결정을 내려도,
그 값을 **실제 모터에 어떻게 쓰느냐**는 따로 있는 문제. 그걸 담당하는 게 `ros2_control`.

```
   MoveIt        ──┐
                   │ JointTrajectory (시간×각도 시퀀스)
                   ▼
   ┌───────────────────────────────────────────────┐
   │  joint_trajectory_controller                  │
   │   - 보내야 할 다음 각도/속도 계산              │
   └────────────────────┬──────────────────────────┘
                        │
                        ▼
   ┌───────────────────────────────────────────────┐
   │  hardware_interface (플러그인)                 │
   │   - mock_components : 가짜로 위치만 반환       │
   │   - feetech_hardware: USB 시리얼로 STS3215    │
   │   - gz_ros2_control : Gazebo 시뮬에 명령       │
   └───────────────────────────────────────────────┘
                        │
                        ▼
                 실제 모터 / 시뮬
```

URDF 안의 `<ros2_control>` 태그에서 어떤 hardware_interface 를 쓸지 정함. 본 repo에서는
[ws/src/ros2_so_arm100/so_arm101_description/control/so_arm101.ros2_control.xacro](../ws/src/ros2_so_arm100/so_arm101_description/control/so_arm101.ros2_control.xacro)
에서 `hardware_type` 인자로 mock / real / gazebo 를 분기.

| hardware_type | 필요 조건 | 용도 |
|---|---|---|
| `mock_components` | 없음 | RViz에서만 확인 — 학습 단계의 기본값 |
| `real` | `/dev/ttyACM0` + STS3215 서보 | 실제 로봇 |
| `gazebo` | gz_ros2_control | 물리 시뮬 |

---

## 3. MoveIt2 — "어떻게 갈지" 계획하는 두뇌

ros2_control 이 "주어진 시간×각도 시퀀스를 그대로 실행" 한다면, MoveIt 은
**그 시퀀스를 처음부터 만든다**. 입력은 "끝단을 이 좌표로 보내" 같은 추상적 목표.

```
   목표 (joint goal 또는 pose goal)
              │
              ▼
   ┌─────────────────────────────────────┐
   │  move_group (MoveIt 메인 노드)       │
   │   - URDF/SRDF 읽음                  │
   │   - kinematics.yaml 의 IK 사용      │
   │   - OMPL 등 플래너로 충돌 없는 경로  │
   │   - 결과: JointTrajectory           │
   └─────────────────────────────────────┘
              │
              ▼ ros2_control 으로 전달
```

핵심 설정 파일 (전부 `*_moveit_config/config/` 안):

| 파일 | 역할 |
|---|---|
| `*.srdf` | URDF에 의미 추가: 어떤 joint 들이 "팔 그룹"이고 어떤 게 "그리퍼"인가, 이름붙은 자세(`zero`, `rest`) |
| `kinematics.yaml` | IK solver 종류 (`KDLKinematicsPlugin` 기본) |
| `joint_limits.yaml` | 속도/가속도 상한 (MoveIt 전용, URDF 와 별개) |
| `ompl_planning.yaml` | 어떤 플래너(RRTConnect 등) 와 그 파라미터 |

Python 에서 MoveIt 에게 명령 보내는 두 가지 방법:
1. **MoveGroup action client** — `moveit_msgs/action/MoveGroup` 으로 보냄. 본 repo의 `soarm101_tutorials` 가 채택할 방식 (PinkWink 스타일).
2. **moveit_py** — Python 바인딩. 좀 더 직접적이지만 의존성이 무거움.

---

## 4. 본 repo 에서의 매핑

### SO-ARM101 의 joint / link 이름 (현재 baseline — LeRobot 표준)

```
base_link ──[shoulder_pan_joint]──▶ shoulder_link
          ──[shoulder_lift_joint]─▶ upper_arm_link
          ──[elbow_flex_joint]────▶ lower_arm_link
          ──[wrist_flex_joint]────▶ wrist_link
          ──[wrist_roll_joint]────▶ gripper_link  (← end-effector)
                                                  └─[gripper_joint]─▶ jaw_link
```

| 시스템 / 표기 | 이름 |
|---|---|
| URDF/SRDF | `shoulder_pan_joint`, `shoulder_lift_joint`, `elbow_flex_joint`, `wrist_flex_joint`, `wrist_roll_joint`, `gripper_joint` |
| 서보 ID | `1`, `2`, `3`, `4`, `5`, `6` |
| Web SDK (`so-arm101-controller`) | `base`, `shoulder`, `elbow`, `wrist_pitch`, `wrist_roll`, `gripper` |
| PinkWink 표기 (참고) | `joint1`, `joint2`, `joint3`, `joint4`, `joint5`, `joint6` |

> 학생은 Phase 3 에서 **URDF/SRDF 의 joint 이름을 `joint1..joint6` 로
> 직접 바꿔보는 실습**을 합니다. 그게 URDF 가 어디서 어떻게 읽히는지
> 가장 빨리 익히는 방법.

### Planning group

- `manipulator` — base_link → gripper_link (팔 5축)
- `gripper` — `gripper_joint` 하나만

### 이름붙은 자세 (SRDF group_state)

| 이름 | 의미 |
|---|---|
| `zero` | 모든 관절 0 — 직립 |
| `rest` | 안전한 보관 자세 |
| `extended` | 팔 펼친 자세 |

---

## 5. 환경 점검 한 줄

```bash
./tools/check_env.sh
```

위 스크립트가 다음을 한 번에 봅니다:
- Ubuntu / ROS2 Jazzy
- `moveit`, `moveit_planners_ompl`, `controller_manager`, `joint_trajectory_controller`
- (선택) `gz_ros2_control`
- 사용자 권한 (`dialout`, `video`)
- `/dev/ttyACM0` 존재 여부

모두 `✓` 면 Phase 2(첫 launch)로 진행 가능.

---

## 6. 다음 단계

- **Phase 1 (격리)** — `ws/src/soarm101_pick_place/` 를
  `ws/src/projects/aruco_pick_place/` 로 이동. 이건 ArUco 기반 응용
  프로젝트이므로 학습 첫 단계와는 분리.
- **Phase 2 (첫 launch)** — RViz 에서 SO-ARM101 처음 보기.
- **Phase 3 (URDF refactor 실습)** — 학생이 `shoulder_pan_joint` →
  `joint1` 변환을 손으로.
- **Phase 4 (ex01-04)** — MoveIt 으로 처음 명령 보내기.

자세한 단계별 진행은 본 repo `README.md` 의 로드맵 표를 참고.
