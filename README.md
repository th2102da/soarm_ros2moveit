# SO-ARM101 + ROS2 Jazzy + MoveIt2

SO-ARM101 6-DOF 로봇암을 ROS2 / MoveIt2 로 제어하기 위한 **학습용 repo**.
규칙기반 web 컨트롤러([sibling repo `so-arm101-controller`](https://github.com/th2102da/so-arm101-controller))
다음 단계로, 같은 로봇을 ROS2 표준 스택 위에서 다시 다룬다.

## 환경

- Ubuntu 24.04
- ROS2 **Jazzy** + MoveIt2 + ros2_control (apt 설치)
- Gazebo **Harmonic** (선택)
- 점검: `./tools/check_env.sh`

## 학습 로드맵 (6-Phase)

| # | Phase | 산출물 | 상태 |
|---|-------|--------|------|
| 0 | 기초 멘탈 모델 | [docs/00_basics.md](docs/00_basics.md), `tools/check_env.sh` | In Progress |
| 1 | 응용 패키지 격리 | `ws/src/projects/aruco_pick_place/` 로 이동, `soarm101_tutorials/` 스캐폴드 | Planned |
| 2 | 첫 launch | `display.launch.py` 로 RViz 에서 SO-ARM101 보기 | Planned |
| 3 | 학생 실습: URDF refactor | `shoulder_pan_joint → joint1` 직접 변환 | Planned |
| 4 | Tutorials ex01-04 | joint_state, named_pose, joint_goal, pose_goal | Planned |
| 5 | Tutorials ex05-09 | cartesian, gripper, **가상** pick&place, constraints, collision | Planned |
| 6 | ArUco 부활 | `projects/aruco_pick_place/` 를 `tutorials.utils` 위로 재작성 | Planned |

각 Phase 의 mental model 은 [docs/00_basics.md](docs/00_basics.md) 참고.

## 현재 패키지

```
ws/src/
├── ros2_so_arm100/              # upstream (JafarAbdi) — URDF / MoveIt / 디스크립션
│   ├── so_arm100_description/
│   ├── so_arm100_moveit_config/  # ← 현재 baseline (so_arm101 전용 config 는 미작성)
│   ├── so_arm101_description/    # URDF + ros2_control xacro
│   ├── so_arm_gz/                # Gazebo 브링업
│   └── so_arm_utils/
├── feetech_ros2_driver/         # upstream — Feetech STS3215 hardware_interface
├── projects/                    # 응용 프로젝트 (Phase 1 이후 채워짐)
└── soarm101_tutorials/          # 학습 예제 패키지 (Phase 1 이후 채워짐)
```

> ⚠ 이전 세션에서 README 가 `so_arm101_moveit_config` 패키지 존재를
> 가정했으나 실제로는 작성되지 않았습니다. Phase 3 이후 학생이 직접
> 만들거나, 그 시점에 별도 패키지로 분리할 수 있습니다.

## 빠른 시작 (현재 가능한 것만)

```bash
# 1. 환경 점검
./tools/check_env.sh

# 2. 빌드
cd ws && colcon build --symlink-install && source install/setup.bash

# 3. URDF 만 RViz 로 보기 (joint_state_publisher_gui 슬라이더로 움직임)
ros2 launch so_arm101_description display.launch.py    # Phase 2 에서 검증
```

MoveIt 데모는 Phase 4 이후 본격적으로 활용.

## 보조 자산

- [hp60c_camera/](hp60c_camera/) — Hiwonder/Angstrong HP60C 뎁스 카메라
  SDK + Python reader. Phase 6 에서 ArUco 픽플레이스에 연결.
- [projects/](projects/) — 빈 슬롯. Phase 1 에서 `aruco_pick_place/` 가 들어옴.

## 참고 자료

- 학습 커리큘럼 골격: [PinkWink/robotarm_tutorials](https://github.com/PinkWink/robotarm_tutorials)
- URDF / MoveIt 베이스: [JafarAbdi/ros2_so_arm100](https://github.com/JafarAbdi/ros2_so_arm100)
- Feetech 드라이버: [JafarAbdi/feetech_ros2_driver](https://github.com/JafarAbdi/feetech_ros2_driver)
