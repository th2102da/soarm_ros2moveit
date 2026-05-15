# 01. ROS2 처음부터 — 새 폴더에서 따라 하기

이 가이드는 **ROS2 를 처음 만지는 사람**이 빈 폴더 하나에서 시작해서,
SO-ARM101 의 URDF 를 RViz 로 띄우고, MoveIt 데모를 돌리고, 자기
ROS2 패키지를 직접 만들기까지 한 번에 따라가도록 만들어졌습니다.

**가정**: Ubuntu **24.04** (`noble`). 다른 OS / 다른 Ubuntu 버전은 안 다룹니다.

**가이드 작업 폴더**: 이 가이드는 `~/ros2_lab/` 이라는 새 폴더에서 진행
합니다. 본 repo `~/soarm_ros2moveit` 과는 **완전히 별개**의 연습 공간이에요.
끝나면 지워도 됩니다.

---

## 0. 한눈에 보는 흐름

```
[0]  ROS2 Jazzy 설치           (apt 한 번)
[1]  bashrc 설정 + 도구 설치    (colcon, rosdep)
[2]  빈 워크스페이스 만들기      mkdir + colcon build
[3]  외부 패키지 받기            git clone × 2
[4]  의존성 해결 + 빌드          rosdep + colcon build
[5]  URDF 를 RViz 로 띄우기      ros2 launch
[6]  MoveIt 데모 돌리기          ros2 launch demo.launch.py
[7]  내 패키지 만들기            ros2 pkg create + 첫 노드
[8]  CLI 둘러보기                ros2 node/topic/service/action
```

각 단계마다 끝에 **확인 체크리스트** 가 있어요. 모두 ✓ 면 다음 단계로.

---

## 1. ROS2 Jazzy 설치

> 이미 깔려 있다면 (`/opt/ros/jazzy` 존재) **2 절로 점프**.

### 1-1. 로캘

영문 로캘이 안 잡혀 있으면 ROS2 빌드 단계에서 경고가 떠요. 미리 정리:

```bash
sudo apt update
sudo apt install -y locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```

### 1-2. ROS2 저장소 추가

```bash
sudo apt install -y software-properties-common curl
sudo add-apt-repository -y universe

sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
    | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
```

### 1-3. 패키지 설치

데스크탑 풀 + 개발 도구 + MoveIt + ros2_control:

```bash
sudo apt update
sudo apt install -y \
    ros-jazzy-desktop \
    ros-dev-tools \
    ros-jazzy-moveit \
    ros-jazzy-ros2-control \
    ros-jazzy-ros2-controllers \
    ros-jazzy-joint-state-publisher-gui \
    ros-jazzy-xacro \
    ros-jazzy-controller-manager \
    ros-jazzy-joint-trajectory-controller
```

용량 ~3 GB. 다운 + 설치까지 보통 10–20 분.

### 1-4. colcon, rosdep, vcstool 설치

ROS2 패키지를 빌드하고 의존성 해결하는 도구들:

```bash
sudo apt install -y \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool

sudo rosdep init
rosdep update
```

> `rosdep init` 이 이미 했다고 에러를 내면 그건 정상 — 무시.

### 1-5. bashrc 설정

매번 터미널 열 때마다 ROS2 환경이 자동으로 잡히도록:

```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

### 1-6. 설치 확인

```bash
printenv ROS_DISTRO    # → jazzy
ros2 doctor            # 빨간 줄 없으면 OK (네트워크 경고 정도는 무시)
```

**체크리스트**
- [ ] `printenv ROS_DISTRO` 가 `jazzy` 를 출력
- [ ] `ros2 --help` 가 사용법을 보여줌
- [ ] `which colcon` 이 경로를 출력

---

## 2. 빈 워크스페이스 만들기

### 2-1. 폴더 만들기

```bash
mkdir -p ~/ros2_lab/src
cd ~/ros2_lab
```

이 시점의 구조:
```
~/ros2_lab/
└── src/          ← 우리 ROS2 패키지들이 들어갈 자리 (비어 있음)
```

### 2-2. 첫 빌드 (빈 워크스페이스)

```bash
colcon build
```

예상 출력:
```
Summary: 0 packages finished
```

(에러 아님 — 그냥 빌드할 게 없다는 뜻)

이러면 `build/`, `install/`, `log/` 세 폴더가 자동 생성돼요:

```
~/ros2_lab/
├── build/        ← colcon 의 중간 산출물
├── install/      ← 빌드된 결과물이 ros2 가 찾는 형태로 정리됨
├── log/          ← 빌드 로그
└── src/
```

### 2-3. install/setup.bash 소싱

빌드한 워크스페이스를 ros2 가 인식하게 하려면 매 터미널마다:

```bash
source ~/ros2_lab/install/setup.bash
```

> 자주 까먹는 단계! 만약 `ros2 launch ...` 가 "package not found" 라고
> 한다면 99% 이 소싱을 안 한 거예요.

### 2-4. 검증

```bash
ros2 pkg list | wc -l    # 시스템 + 워크스페이스 패키지 합산 수 (수백 개)
```

**체크리스트**
- [ ] `~/ros2_lab/{build,install,log,src}` 4 개 폴더 존재
- [ ] `source install/setup.bash` 가 에러 없이 끝남

---

## 3. SO-ARM 외부 패키지 받기

### 3-1. URDF + MoveIt 베이스

```bash
cd ~/ros2_lab/src
git clone https://github.com/JafarAbdi/ros2_so_arm100.git
```

이 한 repo 안에 5 개 ROS2 패키지가 들어있어요:

```
ros2_so_arm100/
├── so_arm100_description/         ← SO-ARM100 URDF + ros2_control xacro
├── so_arm100_moveit_config/       ← MoveIt 설정 (SRDF, kinematics 등)
├── so_arm101_description/         ← SO-ARM101 URDF (우리가 쓸 거)
├── so_arm_gz/                     ← Gazebo 브링업
└── so_arm_utils/                  ← launch 헬퍼
```

### 3-2. Feetech 서보 하드웨어 드라이버

```bash
git clone https://github.com/JafarAbdi/feetech_ros2_driver.git
```

이건 STS3215 모터를 ros2_control 에 연결해주는 C++ hardware_interface.
실제 로봇에 명령을 보낼 때만 필요. **mock 으로만 돌릴 거면 생략 가능**
하지만, 의존성 해결 단계에서 (3-3) 어차피 받게 되니 미리 받아두는 편이 깔끔.

### 3-3. 의존성 해결 (rosdep)

각 패키지의 `package.xml` 안에 적힌 의존성을 자동으로 apt 설치:

```bash
cd ~/ros2_lab
rosdep install --from-paths src --ignore-src -r -y
```

옵션 풀이:
| 옵션 | 의미 |
|---|---|
| `--from-paths src` | `src/` 폴더 안의 모든 `package.xml` 을 훑는다 |
| `--ignore-src` | `src/` 안에 있는 패키지는 의존성으로 치지 않음 (이미 우리가 받았음) |
| `-r` | 일부 실패해도 끝까지 계속 |
| `-y` | 자동 yes |

### 3-4. 빌드

```bash
colcon build --symlink-install
```

`--symlink-install` 은 install/ 안에 파일을 복사하는 대신 심볼릭 링크를
만들어요. 파이썬 노드를 고치면 재빌드 없이 바로 반영돼서 학습 단계에서
편함.

빌드 첫 회는 보통 2–5 분.

### 3-5. 소싱 + 확인

```bash
source install/setup.bash
ros2 pkg list | grep so_arm
```

예상 출력:
```
so_arm100_description
so_arm100_moveit_config
so_arm101_description
so_arm_gz
so_arm_utils
```

**체크리스트**
- [ ] 위 5 개 패키지 모두 보임
- [ ] `colcon build` 가 빨간색 ERROR 없이 끝남

> ⚠ 경고(WARNING) 한두 개는 흔해요. 무시.

---

## 4. URDF 를 RViz 로 띄우기 — 첫 결과물

```bash
ros2 launch so_arm101_description view_description.launch.py rviz:=true
```

🚨 `rviz:=true` **빼먹지 마세요** — 이 launch 파일의 RViz 기본값이
`false` 라 그냥 띄우면 슬라이더 GUI 만 보이고 3D 화면이 안 떠요.

새 창에서 **RViz** 가 뜨면서 SO-ARM101 의 3D 모델이 보입니다. 그리고
**Joint State Publisher GUI** 라는 작은 슬라이더 창이 같이 떠요.

```
┌─────────────────┐   ┌──────────────────────────┐
│ Joint State GUI │   │ RViz                     │
│                 │   │                          │
│ shoulder_pan ━│  │   │   [SO-ARM101 3D 모델]    │
│ shoulder_lift━│  │   │                          │
│ elbow_flex ━━│   │   │                          │
│ wrist_flex ━━│   │   │                          │
│ wrist_roll ━━│   │   │                          │
│ gripper ━━━━│   │   │                          │
└─────────────────┘   └──────────────────────────┘
```

슬라이더를 움직이면 RViz 의 모델이 실시간으로 따라 움직입니다. **이게 첫
ROS2 결과물** — 토픽 `/joint_states` 에 슬라이더 값이 발행되고, RViz 가
그걸 받아서 그림.

확인용:
```bash
# 새 터미널 (소싱 필수)
source ~/ros2_lab/install/setup.bash
ros2 topic list
ros2 topic echo /joint_states
```

`/joint_states` 토픽이 1초에 여러 번 출력되면 OK.

종료: launch 가 떠있는 터미널에서 **Ctrl+C**.

**체크리스트**
- [ ] RViz 에 SO-ARM101 이 보임
- [ ] 슬라이더 움직이면 모델이 움직임
- [ ] `ros2 topic list` 에 `/joint_states` 보임

---

## 5. MoveIt 데모 돌리기

MoveIt 의 "Motion Planning" 패널로 자세를 끌어서 경로 계획 받아보기.

```bash
ros2 launch so_arm100_moveit_config demo.launch.py hardware_type:=mock_components
```

🚨 `hardware_type:=mock_components` **꼭 같이 넘기세요** — 이 launch 는
`hardware_type` 에 기본값이 없어서 빼면 즉시 죽어요. 옵션은
`mock_components` (가짜) / `real` (실 로봇) / `gazebo`. 학습 단계에선 mock.

> 잠깐 — SO-ARM**101** 모델인데 왜 `so_arm**100**_moveit_config` 를 쓰는지?
> upstream repo 는 SO-ARM100 용 MoveIt config 만 제공하고 101 전용은
> 아직 없어요. URDF 가 거의 같아서 100 용으로도 101 의 mock 동작을 볼 수
> 있습니다. 학습 중반쯤(우리 repo 의 Phase 3) 에 학생이 직접 101 용
> moveit_config 를 만들 거예요.

RViz 에서 보이는 것:
- 왼쪽 패널 **MotionPlanning** Display 추가됨
- 컬러풀한 화살표 위젯이 그리퍼에 붙어 있음 — 끌어서 목표 자세 설정
- `Plan` 버튼: 충돌 없는 경로 찾기
- `Execute` 버튼: 그 경로 실행 (mock 이라 시각적으로만 움직임)

3 분 안에 시도해볼 것:
1. 화살표를 살짝 끌어 RViz 위 공간 어딘가로
2. `Plan` 클릭 → 무지개색 trajectory 가 보임
3. `Execute` → 모델이 그 trajectory 를 따라 움직임

종료: Ctrl+C.

**체크리스트**
- [ ] MotionPlanning 패널이 RViz 에 있음
- [ ] Plan 이 성공 (가끔 IK 실패 — 다른 위치로 시도)
- [ ] Execute 후 모델이 움직임

---

## 6. 내 ROS2 패키지 직접 만들기

이제 외부 패키지가 아닌 **본인 패키지** 를 처음부터 만들어요.

### 6-1. 패키지 생성

```bash
cd ~/ros2_lab/src
ros2 pkg create --build-type ament_python my_first_pkg \
    --dependencies rclpy std_msgs
```

생성된 구조:
```
my_first_pkg/
├── my_first_pkg/
│   └── __init__.py
├── resource/
│   └── my_first_pkg
├── test/
├── package.xml          ← 메타데이터 + 의존성
├── setup.cfg
└── setup.py             ← 빌드/엔트리포인트 정의
```

### 6-2. 첫 노드 작성

`~/ros2_lab/src/my_first_pkg/my_first_pkg/hello_node.py` 만들기:

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class HelloNode(Node):
    def __init__(self):
        super().__init__('hello_node')
        self.pub = self.create_publisher(String, '/hello', 10)
        self.timer = self.create_timer(1.0, self.tick)
        self.count = 0

    def tick(self):
        msg = String()
        msg.data = f'hello ROS2 #{self.count}'
        self.pub.publish(msg)
        self.get_logger().info(msg.data)
        self.count += 1


def main():
    rclpy.init()
    node = HelloNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### 6-3. setup.py 에 entry_point 등록

`ros2 run` 으로 실행하려면 `setup.py` 의 `entry_points` 에 등록 필요:

```python
# setup.py 의 entry_points 부분만 발췌
entry_points={
    'console_scripts': [
        'hello_node = my_first_pkg.hello_node:main',
    ],
},
```

### 6-4. 빌드 + 소싱

```bash
cd ~/ros2_lab
colcon build --packages-select my_first_pkg --symlink-install
source install/setup.bash
```

`--packages-select` 는 그 패키지만 빌드 (다른 패키지 다시 빌드 안 함).

### 6-5. 실행

```bash
ros2 run my_first_pkg hello_node
```

예상 출력:
```
[INFO] [hello_node]: hello ROS2 #0
[INFO] [hello_node]: hello ROS2 #1
[INFO] [hello_node]: hello ROS2 #2
...
```

다른 터미널 (소싱 후):
```bash
ros2 topic echo /hello
```

`/hello` 토픽으로 같은 메시지가 흘러오는 게 보임. **이게 노드 간 통신의
가장 기본 패턴.**

종료: Ctrl+C.

**체크리스트**
- [ ] `ros2 run my_first_pkg hello_node` 가 1 초마다 로그 찍음
- [ ] 다른 터미널에서 `ros2 topic echo /hello` 가 같은 메시지를 받음

---

## 7. ROS2 CLI 둘러보기

`hello_node` 가 떠있는 상태에서 다른 터미널 (소싱 후) 에서 시도:

### 노드

```bash
ros2 node list                # 떠있는 노드들
ros2 node info /hello_node    # 그 노드가 발행/구독하는 토픽
```

### 토픽

```bash
ros2 topic list                       # 발행되고 있는 모든 토픽
ros2 topic info /hello                # 이 토픽의 메시지 타입
ros2 topic echo /hello                # 실시간 값 보기
ros2 topic hz /hello                  # 발행 주파수
ros2 topic pub /hello std_msgs/msg/String "data: 'from CLI'" --once
```

### 서비스

```bash
ros2 service list
ros2 service type /clear              # 예: gz 환경에서
```

### 액션 (오래 걸리는 요청 — MoveIt 이 이걸로 동작)

```bash
ros2 action list                      # MoveIt 켜져 있으면 /move_action 등이 보임
ros2 action info /move_action
```

이 4 가지(node/topic/service/action) 가 ROS2 의 전부. 외워두면
디버깅이 쉬워요.

---

## 8. 흔한 함정 — 안 풀리면 이거부터 봐

| 증상 | 원인 / 조치 |
|---|---|
| `ros2 launch …` → "Package 'X' not found" | **소싱 안 함**. `source ~/ros2_lab/install/setup.bash` |
| `colcon build` → "rosdep keys missing" | `rosdep install --from-paths src --ignore-src -r -y` 누락 |
| 새 터미널마다 ros2 명령이 안 먹음 | `~/.bashrc` 에 `source /opt/ros/jazzy/setup.bash` 빠짐 |
| `ros2 run my_pkg my_node` → "executable not found" | `setup.py` 의 `entry_points` 등록 누락 또는 빌드 안 함 |
| Python 노드 고쳤는데 반영 안 됨 | `--symlink-install` 없이 빌드한 경우. 다시 `colcon build --symlink-install` |
| 빌드는 됐는데 RViz 가 검은 화면 | URDF 패스 잘못 잡힘. launch 의 `description_package` 인자 확인 |
| MoveIt Plan 이 항상 실패 | 목표 자세가 IK 범위 밖 — RViz 의 화살표 위젯을 조금만 움직여서 다시 시도 |
| `colcon build` 가 갑자기 옛 패키지를 다시 찾음 | `~/ros2_lab/build,install,log` 를 통째로 지우고 다시 빌드 (`rm -rf build install log && colcon build`) |

---

## 9. 다음 단계

여기까지가 ROS2 의 기초 전부. 이 가이드를 끝낸 사람이 이제 할 수 있는 것:

- 외부 ROS2 패키지를 받아서 빌드
- URDF 를 RViz 로 띄움
- MoveIt 데모를 mock 으로 돌림
- 자기 ROS2 파이썬 패키지를 만들고 노드 실행
- 토픽/서비스/액션을 CLI 로 조사

이 다음은 본 repo (`~/soarm_ros2moveit`) 로 돌아와서:

- **Phase 2** — 본 repo 의 `ws/` 안에서 같은 흐름을 재현 (`colcon build`, `source`, `view_description.launch.py`)
- **Phase 3** — URDF 안의 joint 이름을 `shoulder_pan_joint` → `joint1` 로 학생이 직접 refactor 하는 실습
- **Phase 4 이후** — `soarm101_tutorials/` 패키지 안에 `ex01..ex09` 작성 (PinkWink 커리큘럼 미러)

전체 로드맵은 [README.md](../README.md) 의 6-Phase 표 참고.

---

## 부록 A — 한 줄로 다 정리

```bash
# 0. (한 번만) ROS2 + 도구 설치 — 1-1 ~ 1-5 절 참고
# 1. 새 워크스페이스
mkdir -p ~/ros2_lab/src && cd ~/ros2_lab

# 2. 외부 패키지
cd src
git clone https://github.com/JafarAbdi/ros2_so_arm100.git
git clone https://github.com/JafarAbdi/feetech_ros2_driver.git
cd ..

# 3. 의존성 + 빌드
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash

# 4. URDF in RViz
ros2 launch so_arm101_description view_description.launch.py rviz:=true

# 5. MoveIt 데모
ros2 launch so_arm100_moveit_config demo.launch.py hardware_type:=mock_components
```

---

## 부록 B — 이 가이드를 끝낸 뒤 `~/ros2_lab/` 정리

연습 폴더라 그대로 지워도 됩니다:

```bash
rm -rf ~/ros2_lab
```

본 repo (`~/soarm_ros2moveit`) 와는 무관하므로 영향 없음.
