# 자주 쓰는 명령어

## 실행

```bash
# MoveIt Demo (시뮬레이션, RViz에서 조작)
ros2 launch so_arm101_moveit_config demo.launch.py hardware_type:=mock_components

# 실제 하드웨어
ros2 launch so_arm101_moveit_config demo.launch.py hardware_type:=real usb_port:=/dev/ttyACM0

# MoveIt만 (RViz 없이)
ros2 launch so_arm101_moveit_config move_group.launch.py

# RViz만 (MoveIt 시각화)
ros2 launch so_arm101_moveit_config moveit_rviz.launch.py

# 컨트롤러만 (MoveIt 없이)
ros2 launch so_arm101_description controllers_bringup.launch.py hardware_type:=mock_components
```

## 모니터링

```bash
# 컨트롤러 상태
ros2 control list_controllers

# 하드웨어 인터페이스
ros2 control list_hardware_interfaces

# 조인트 상태
ros2 topic echo /joint_states

# TF tree 시각화
ros2 run tf2_tools view_frames

# rqt 조인트 슬라이더
ros2 run rqt_joint_trajectory_controller rqt_joint_trajectory_controller
```

## 빌드

```bash
# 전체 빌드
cd ~/soarm101_ros2_moveit/ws && colcon build --symlink-install

# 특정 패키지만
colcon build --symlink-install --packages-select so_arm101_moveit_config

# 빌드 후 source
source ~/soarm101_ros2_moveit/ws/install/setup.bash
```

## 디버깅

```bash
# 패키지 경로 확인
ros2 pkg prefix so_arm101_moveit_config
ros2 pkg prefix so_arm101_description

# URDF 확인
ros2 topic echo /robot_description --once | head -50

# launch 파일 찾기
ros2 pkg executables so_arm101_moveit_config
```
