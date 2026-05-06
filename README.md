# SO-ARM101 + ROS2 Jazzy + MoveIt2

SO-ARM101 로봇암을 ROS2 MoveIt2로 제어하기 위한 프로젝트.

## 프로젝트 로드맵

| # | 프로젝트 | 상태 |
|---|----------|------|
| 1 | MoveIt2 기본 셋업 | Done |
| 2 | ArUco Pick & Place | In Progress |
| 3 | LeRobot + ROS2 모방학습 | Planned |
| 4 | MoveIt Task Constructor | Planned |

## 빠른 시작

```bash
# MoveIt Demo (시뮬레이션)
ros2 launch so_arm101_moveit_config demo.launch.py hardware_type:=mock_components

# ArUco Pick & Place (카메라 + MoveIt)
ros2 launch soarm101_pick_place pick_place.launch.py hardware_type:=mock_components

# 카메라 + ArUco 감지만 (MoveIt 없이)
ros2 launch soarm101_pick_place camera_aruco.launch.py
```

## 프로젝트 구조

```
soarm101_ros2_moveit/
├── README.md
├── docs/
│   ├── 01_setup_guide.md           # ROS2 + MoveIt2 설치 가이드
│   ├── 02_package_structure.md     # 아키텍처 다이어그램
│   ├── 03_troubleshooting.md       # 트러블슈팅
│   ├── 04_quick_commands.md        # 자주 쓰는 명령어
│   └── 05_pick_place_project.md    # ArUco Pick & Place 가이드
├── examples/
│   ├── moveit_basic.py             # Joint goal 예제
│   └── moveit_pose_goal.py         # Pose goal 예제
├── tools/
│   └── generate_aruco_markers.py   # ArUco 마커 이미지 생성
├── aruco_markers_sheet.png         # 인쇄용 마커 시트
└── ws/src/
    ├── ros2_so_arm100/             # URDF + MoveIt configs
    │   ├── so_arm101_description/  # SO-ARM101 6-DOF URDF
    │   ├── so_arm101_moveit_config/# MoveIt2 config (우리가 생성)
    │   └── ...
    ├── feetech_ros2_driver/        # STS3215 서보 드라이버
    └── soarm101_pick_place/        # ArUco Pick & Place 패키지
        ├── camera_bridge_node.py   # shm → ROS2 이미지
        ├── aruco_detector_node.py  # ArUco 감지 + 좌표 변환
        ├── pick_place_node.py      # MoveIt2 pick & place
        └── calibrate_hand_eye_node.py
```

## 참고 자료

- [ros2_so_arm100](https://github.com/JafarAbdi/ros2_so_arm100)
- [feetech_ros2_driver](https://github.com/JafarAbdi/feetech_ros2_driver)
- [lerobot-ros](https://github.com/ycheng517/lerobot-ros) (프로젝트 3용)
