# 트러블슈팅 가이드

## 빌드 관련

### rosdep install 에러
```bash
# rosdep 초기화 안 된 경우
sudo rosdep init
rosdep update

# 특정 패키지 못 찾는 경우 (-r로 무시하고 계속)
rosdep install --from-paths src --ignore-src -r -y
```

### colcon build 에러 — feetech_ros2_driver
```bash
# serial 관련 헤더 없을 때
sudo apt install -y libserial-dev

# hardware_interface 관련
sudo apt install -y ros-jazzy-hardware-interface ros-jazzy-controller-manager
```

### nav2_common 못 찾을 때
```bash
sudo apt install -y ros-jazzy-nav2-common
```

## 실행 관련

### "Could not find package so_arm101_moveit_config"
```bash
# 빌드 후 source 안 했을 때
source ~/soarm101_ros2_moveit/ws/install/setup.bash

# bashrc에 추가
echo "source ~/soarm101_ros2_moveit/ws/install/setup.bash" >> ~/.bashrc
```

### USB 권한 에러
```bash
# 일시적 해결
sudo chmod 666 /dev/ttyACM0

# 영구적 해결 — udev rule
echo 'SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", MODE="0666", SYMLINK+="LeRobotFollower"' \
  | sudo tee /etc/udev/rules.d/99-lerobot.rules
sudo udevadm control --reload-rules && sudo udevadm trigger

# 또는 사용자를 dialout 그룹에 추가
sudo usermod -aG dialout $USER
# (로그아웃 후 재로그인 필요)
```

### Controller spawner 타임아웃
```bash
# controller_manager가 아직 안 뜬 상태 — 기다리거나 수동으로
ros2 control list_controllers
ros2 control list_hardware_interfaces
```

### MoveIt "No valid IK solution"
- SRDF의 tip_link가 URDF와 일치하는지 확인
- joint_limits.yaml 범위가 URDF와 일치하는지 확인
- KDL solver timeout 늘리기 (kinematics.yaml에서 0.05로)

### RViz에서 로봇이 안 보일 때
- Fixed Frame이 "world"로 설정되어 있는지 확인
- robot_state_publisher가 실행 중인지: `ros2 topic echo /robot_description`
- TF tree 확인: `ros2 run tf2_tools view_frames`

## 서보 관련

### STS3215 baudrate 문제
기본 baudrate는 1,000,000 (1Mbps). 다른 값으로 설정된 서보가 있으면 통신 실패.
```bash
# feetech_ros2_driver demo로 개별 서보 테스트
# (빌드 후)
ros2 run feetech_ros2_driver demo --ros-args -p usb_port:=/dev/ttyACM0
```

### 서보 ID 확인/변경
lerobot 도구 사용:
```bash
python -m lerobot.scripts.configure_motor --port /dev/ttyACM0 --brand feetech
```
