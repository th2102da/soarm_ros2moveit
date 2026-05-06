# 프로젝트 2: ArUco Pick & Place

## 개요

ArUco 마커가 부착된 물체를 감지하여 MoveIt2로 pick & place 수행.

```
[ASC60C 카메라] → shm_bridge → [camera_bridge_node] → ROS2 Image topics
                                          ↓
                              [aruco_detector_node] → /aruco/poses, /tf
                                          ↓
                              [pick_place_node] → MoveIt2 → 로봇 제어
```

## 사전 준비

### 1. ArUco 마커 준비
- **Dictionary**: DICT_4X4_50
- **크기**: 30mm × 30mm
- **ID**: 0, 1, 2, 3 (물체별)
- 인쇄 후 물체에 부착

마커 생성:
```python
import cv2
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
for i in range(4):
    img = cv2.aruco.generateImageMarker(aruco_dict, i, 200)
    cv2.imwrite(f"aruco_{i}.png", img)
```

### 2. 카메라 캘리브레이션 (이미 완료)
- `config/camera_intrinsics.yaml` — fx=619.7, fy=622.0
- `config/cam_to_robot.yaml` — hand-eye 변환 (RMSE 24.2mm)

### 3. shm_bridge 준비
```bash
# 기존 soarm_project에서 복원 (휴지통에서)
cp -r ~/.local/share/Trash/files/soarm_project/camera_bridge ~/soarm_project/camera_bridge
cp ~/.local/share/Trash/files/soarm_project/start_camera.sh ~/soarm_project/
```

## 실행 방법

### Step 1: 카메라 시작
```bash
# 터미널 1
echo '1234' | sudo -S bash ~/soarm_project/start_camera.sh
```

### Step 2: 전체 시스템 실행
```bash
# 터미널 2 — 시뮬레이션 (카메라만 실제)
ros2 launch soarm101_pick_place pick_place.launch.py hardware_type:=mock_components

# 또는 실제 하드웨어
ros2 launch soarm101_pick_place pick_place.launch.py hardware_type:=real
```

### 카메라+감지만 테스트 (MoveIt 없이)
```bash
ros2 launch soarm101_pick_place camera_aruco.launch.py
```

## 단계별 개발

### Phase 1: 카메라 파이프라인 검증
1. `camera_bridge_node` 실행
2. `ros2 topic echo /camera/color/image_raw --once` 로 이미지 확인
3. `rqt_image_view`로 시각적 확인

### Phase 2: ArUco 감지 검증
1. `aruco_detector_node` 실행
2. ArUco 마커를 카메라 앞에 놓기
3. `ros2 topic echo /aruco/poses` 로 위치 확인
4. `/aruco/image` 토픽으로 디버그 이미지 확인
5. RViz에서 TF 시각화 (aruco_0, aruco_1 등)

### Phase 3: Pick & Place 실행
1. `pick_place_node`와 MoveIt demo 함께 실행
2. 마커가 감지되면 자동으로 pick & place 시퀀스 실행

## 패키지 구조

```
soarm101_pick_place/
├── config/
│   ├── camera_intrinsics.yaml    # 카메라 내부 파라미터
│   └── cam_to_robot.yaml         # 카메라→로봇 변환
├── launch/
│   ├── pick_place.launch.py      # 전체 시스템
│   └── camera_aruco.launch.py    # 카메라+감지만
└── soarm101_pick_place/
    ├── camera_bridge_node.py     # shm → ROS2
    ├── aruco_detector_node.py    # ArUco 감지 + 좌표 변환
    ├── pick_place_node.py        # MoveIt2 pick & place
    └── calibrate_hand_eye_node.py # 캘리브레이션 (재교정 시)
```

## ROS2 토픽

| 토픽 | 타입 | 설명 |
|------|------|------|
| `/camera/color/image_raw` | sensor_msgs/Image | RGB 이미지 (640×480) |
| `/camera/depth/image_raw` | sensor_msgs/Image | Depth 이미지 (640×480, uint16 mm) |
| `/camera/camera_info` | sensor_msgs/CameraInfo | 카메라 내부 파라미터 |
| `/aruco/poses` | geometry_msgs/PoseArray | 감지된 마커 위치 (로봇 좌표계) |
| `/aruco/image` | sensor_msgs/Image | 마커가 그려진 디버그 이미지 |

## 다음 단계 (프로젝트 4: LeRobot + ROS2)

Pick & Place가 동작하면:
1. `lerobot-ros` 패키지로 텔레옵 데이터 수집
2. LeRobot ACT/Diffusion Policy 학습
3. 학습된 정책을 ROS2로 배포

## 다음 단계 (프로젝트 5: MoveIt Task Constructor)

Pick & Place 시퀀스를 MTC로 재구성:
1. MTC 스테이지 기반 태스크 정의
2. 여러 물체 순차 처리
3. 실패 시 자동 재시도
