# 패키지 구조 상세

## 전체 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    MoveIt2 move_group                   │
│  (motion planning, collision checking, kinematics)      │
├─────────────────────────────────────────────────────────┤
│              joint_trajectory_controller                │
│         (ros2_control JointTrajectoryController)        │
├─────────────────────────────────────────────────────────┤
│               ros2_control_node                         │
│  ┌──────────────────┐  ┌──────────────────────────────┐ │
│  │ mock_components/  │  │ feetech_ros2_driver/         │ │
│  │ GenericSystem     │  │ FeetechHardwareInterface     │ │
│  │ (시뮬레이션)       │  │ (실제 하드웨어)               │ │
│  └──────────────────┘  └──────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│              USB Serial (/dev/ttyACM0)                  │
│              Feetech STS3215 × 6                        │
└─────────────────────────────────────────────────────────┘
```

## 각 패키지 역할

### so_arm101_description
- **URDF/XACRO**: 로봇 기구학 모델 (링크, 조인트, 메시)
- **ros2_control XACRO**: 하드웨어 인터페이스 설정 (mock/real/gazebo/mujoco)
- **controllers YAML**: joint_trajectory_controller, gripper_controller 설정
- **launch**: controllers_bringup.launch.py (ros2_control + robot_state_publisher)

### so_arm101_moveit_config (우리가 생성)
- **SRDF**: 조인트 그룹(manipulator, gripper), 명명된 포즈(zero, rest, extended), collision 제외
- **kinematics.yaml**: KDL IK solver 설정
- **joint_limits.yaml**: 속도/가속도 제한 (MoveIt용)
- **ompl_planning.yaml**: OMPL 플래너 설정
- **trajectory_execution.yaml**: 경로 실행 설정
- **launch**: demo, move_group, moveit_rviz

### feetech_ros2_driver
- **C++ ros2_control plugin**: FeetechHardwareInterface
- **feetech_driver 라이브러리**: serial 통신, STS3215 프로토콜
- 서보 ID, offset, P 계수 등은 ros2_control XACRO에서 설정

### so_arm_utils
- **MoveItConfigs**: robot_name으로 description/moveit_config 패키지를 자동 매핑
- **launch_utils**: xacro 로딩, launch configuration 데코레이터

## 주요 파일 경로

```
# URDF (xacro)
ws/src/ros2_so_arm100/so_arm101_description/urdf/so_arm101.urdf.xacro     # 최상위
ws/src/ros2_so_arm100/so_arm101_description/urdf/so_arm101_macro.xacro     # 매크로 (링크/조인트)

# ros2_control 설정
ws/src/ros2_so_arm100/so_arm101_description/control/so_arm101.ros2_control.xacro  # HW interface
ws/src/ros2_so_arm100/so_arm101_description/control/ros2_controllers.yaml          # controller params

# MoveIt 설정
ws/src/ros2_so_arm100/so_arm101_moveit_config/config/so_arm101.srdf       # 시맨틱 로봇 기술
ws/src/ros2_so_arm100/so_arm101_moveit_config/config/kinematics.yaml      # IK solver
ws/src/ros2_so_arm100/so_arm101_moveit_config/config/joint_limits.yaml    # 조인트 제한
ws/src/ros2_so_arm100/so_arm101_moveit_config/config/ompl_planning.yaml   # 플래너

# 메시 파일
ws/src/ros2_so_arm100/so_arm101_description/meshes/*.stl                  # 3D 모델
```

## hardware_type 옵션

| 값 | 설명 | 필요 조건 |
|----|------|----------|
| `mock_components` | RViz에서만 동작, 실제 하드웨어 불필요 | 없음 |
| `real` | USB로 실제 서보 제어 | USB 어댑터 + STS3215 서보 |
| `gazebo` | Gazebo 시뮬레이션 | gz_ros2_control |
| `mujoco` | MuJoCo 시뮬레이션 | mujoco_ros2_control |
