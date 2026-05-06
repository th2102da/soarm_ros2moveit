# hp60c_camera

Hiwonder가 유통하고 **Angstrong 이 제조한 HP60C / ASC60C 뎁스카메라**를 Linux에서
**RGB + Depth 둘 다** 받아 쓰기 위한 작은 패키지입니다.

이 카메라는 USB로 잡히고 `/dev/video*` 노드도 만들지만, **UVC 표준을 따르지 않아 OpenCV
`VideoCapture` 같은 일반 도구로는 검은 화면만 나옵니다.** 제조사 C++ SDK를 거쳐야 하는데,
SDK가 `std::list`/콜백을 그대로 노출하는 C++ API라 Python에서 `ctypes`만으로는 깔끔히
못 쓰입니다.

이 패키지는 그 사이를 이렇게 메웁니다:

```
   [HP60C USB]
        │
        ▼
  ┌───────────────────────┐
  │ shm_bridge (C++ 데몬) │   Angstrong SDK Listener 패턴으로 카메라 핸들 획득
  │   - SDK 콜백 수신      │   매 프레임 RGB(BGR uint8) + Depth(uint16 mm) 를
  │   - mmap에 프레임 쓰기 │   /dev/shm/hp60c_frames 에 동기화
  └─────────┬─────────────┘
            │  POSIX shared memory (/dev/shm/hp60c_frames)
            ▼
  ┌───────────────────────┐
  │ hp60c_camera (Python) │   numpy + mmap 으로 zero-copy 읽기
  │   CameraReader.read() │   다른 언어에서도 같은 SHM 레이아웃으로 접근 가능
  └───────────────────────┘
```

설계 의도:

- 카메라 SDK 의존성을 **C++ 바이너리 하나에만 가둔다.** Python 쪽은 numpy 만 있으면 됨.
- 여러 프로세스가 동시에 `read()` 가능 (read-only mmap).
- shm_bridge 가 죽어도 다음 실행에서 같은 경로로 다시 붙기만 하면 됨.
- 다른 언어/노드(예: ROS2, Rust)에서도 같은 `/dev/shm/hp60c_frames` 를 그대로 읽을 수 있다.

## 디렉토리 구조

```
hp60c_camera/
├── bridge/               # C++ shm_bridge (SDK -> SHM)
│   ├── CMakeLists.txt
│   ├── shm_bridge.cpp
│   └── build.sh
├── hp60c_camera/         # Python 패키지 (SHM -> numpy)
│   ├── __init__.py
│   └── reader.py
├── examples/
│   ├── 01_open_camera.py
│   └── 02_rgb_and_depth.py
├── scripts/
│   └── start_bridge.sh
├── docs/
│   ├── architecture.md
│   └── troubleshooting.md
└── pyproject.toml
```

## 사전 준비

### 1. Angstrong HP60C SDK 다운로드

라이선스 문제로 이 저장소에는 SDK가 포함되어 있지 않습니다. 별도 경로(예: `~/hp60c_sdk/`)에
SDK 원본을 풀어두면 다음 구조가 있어야 합니다:

```
hp60c_sdk/linux_ros/linux/
├── libs/
│   ├── include/                 (as_camera_sdk_api.h, as_camera_sdk_def.h ...)
│   └── lib/x86_64-linux-gnu/libAngstrongCameraSdk.so
└── configurationfiles/          (hp60c_*.cfg / vega_*.cfg)
```

환경변수로 알려줍니다:

```bash
export HP60C_SDK_DIR=$HOME/hp60c_sdk/linux_ros/linux
```

### 2. shm_bridge 빌드 (C++)

```bash
cd bridge
./build.sh
# -> bridge/build/shm_bridge 생성
```

### 3. Python 의존성

```bash
pip install -e .                     # numpy 만 사용
pip install -e ".[examples]"         # OpenCV 예제까지
```

## 실행

```bash
# 터미널 A: 카메라를 열고 SHM 에 프레임을 흘린다 (포그라운드 실행)
./scripts/start_bridge.sh

# 터미널 B: 프레임을 읽어서 화면에 표시
python examples/01_open_camera.py
python examples/02_rgb_and_depth.py
```

`shm_bridge` 가 카메라를 인식하면 콘솔에 다음과 같이 찍힙니다:

```
[shm_bridge] Camera attached, model type: 9
[shm_bridge] Using config: .../configurationfiles/vega_xxxx.cfg
[shm_bridge] IR : fx=423.1 fy=422.7 cx=320.8 cy=235.8
[shm_bridge] RGB: fx=568.8 fy=568.3 cx=331.6 cy=230.0
[shm_bridge] Streaming started.
```

`/tmp/hp60c_params.txt` 에 IR/RGB intrinsic 도 같이 기록됩니다.

## Python API

```python
from hp60c_camera import CameraReader

with CameraReader() as cam:
    rgb, depth, frame_id = cam.read()           # 즉시
    rgb, depth, frame_id = cam.read_blocking()  # 새 프레임 도착까지 대기
    # rgb   : np.uint8  (H, W, 3)  BGR
    # depth : np.uint16 (H, W)     mm; 0 = invalid
```

자세한 SHM 레이아웃과 동작 원리는 [docs/architecture.md](docs/architecture.md) 참고.
문제가 생기면 [docs/troubleshooting.md](docs/troubleshooting.md) 부터 보세요.

## 라이선스

이 저장소의 코드는 MIT 라이선스. **HP60C SDK 본체는 포함되어 있지 않으며 Angstrong 의 라이선스를
따릅니다.**
