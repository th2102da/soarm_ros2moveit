# SO-ARM101 + ROS2 Jazzy + MoveIt2 셋업 가이드

## 환경
- Ubuntu 24.04 LTS (Noble)
- ROS2 Jazzy Jalisco
- MoveIt2

## 1. ROS2 Jazzy 설치

```bash
# locale 설정
sudo apt update && sudo apt install -y locales software-properties-common curl
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

# ROS2 GPG key + repository
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# ROS2 Desktop (RViz, rqt, demos 포함) + 개발 도구
sudo apt update
sudo apt install -y ros-jazzy-desktop ros-dev-tools

# 환경 자동 로드
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source /opt/ros/jazzy/setup.bash
```

## 2. MoveIt2 설치

```bash
sudo apt install -y ros-jazzy-moveit
```

## 3. 워크스페이스 구성

```bash
mkdir -p ~/soarm101_ros2_moveit/ws/src
cd ~/soarm101_ros2_moveit/ws/src

# 핵심 패키지 클론
git clone https://github.com/JafarAbdi/ros2_so_arm100.git
git clone https://github.com/JafarAbdi/feetech_ros2_driver.git
```

## 4. ROS 의존성 설치 + 빌드

```bash
cd ~/soarm101_ros2_moveit/ws

# rosdep 초기화 (최초 1회)
sudo rosdep init
rosdep update

# 의존성 설치
rosdep install --from-paths src --ignore-src -r -y

# 빌드
colcon build --symlink-install
source install/setup.bash
```

## 5. 실행 (Mock / 시뮬레이션)

```bash
# Mock (RViz만, 하드웨어 불필요)
ros2 launch so_arm101_moveit_config demo.launch.py hardware_type:=mock_components

# MoveIt RViz에서 MotionPlanning 플러그인으로 로봇 조작 가능
```

## 6. 실행 (실제 하드웨어)

```bash
# USB 포트 확인
ls /dev/ttyACM* /dev/ttyUSB*

# udev rule 설정 (optional)
# sudo vim /etc/udev/rules.d/99-lerobot.rules
# SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="55d4", SYMLINK+="LeRobotFollower"

# 실행
ros2 launch so_arm101_moveit_config demo.launch.py hardware_type:=real usb_port:=/dev/ttyACM0
```

## 패키지 구조

```
soarm101_ros2_moveit/
├── docs/                          # 문서
│   ├── 01_setup_guide.md          # 이 파일
│   ├── 02_package_structure.md    # 패키지 구조 설명
│   └── 03_troubleshooting.md      # 트러블슈팅
└── ws/                            # ROS2 워크스페이스
    └── src/
        ├── ros2_so_arm100/        # 메인 패키지 (JafarAbdi)
        │   ├── so_arm100_description/      # SO-ARM100 URDF + controllers
        │   ├── so_arm100_moveit_config/    # SO-ARM100 MoveIt config
        │   ├── so_arm101_description/      # SO-ARM101 URDF + controllers (6-DOF)
        │   ├── so_arm101_moveit_config/    # SO-ARM101 MoveIt config (우리가 생성)
        │   ├── so_arm_gz/                  # Gazebo 시뮬레이션
        │   └── so_arm_utils/               # launch 유틸리티
        └── feetech_ros2_driver/   # Feetech STS3215 서보 드라이버
```

## SO-ARM101 조인트 매핑

| 조인트 이름 | 서보 ID | 기능 | 범위 (rad) |
|-------------|---------|------|------------|
| shoulder_pan_joint | 1 | base 회전 | -1.92 ~ 1.92 |
| shoulder_lift_joint | 2 | 어깨 | -1.75 ~ 1.75 |
| elbow_flex_joint | 3 | 팔꿈치 | -1.69 ~ 1.54 |
| wrist_flex_joint | 4 | 손목 굽힘 | -1.60 ~ 1.60 |
| wrist_roll_joint | 5 | 손목 회전 | -2.30 ~ 2.30 |
| gripper_joint | 6 | 그리퍼 | 0.00 ~ 1.70 |

## 핵심 ROS2 토픽/서비스

```bash
# 조인트 상태 확인
ros2 topic echo /joint_states

# 컨트롤러 목록
ros2 control list_controllers

# MoveIt으로 목표 전송 (Python 예제는 별도 문서 참고)
```
