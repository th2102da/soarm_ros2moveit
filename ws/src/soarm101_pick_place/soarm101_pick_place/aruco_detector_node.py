#!/usr/bin/env python3
"""ArUco 마커 감지 노드

카메라 이미지에서 ArUco 마커를 감지하고,
depth 데이터와 hand-eye 캘리브레이션으로 로봇 좌표계 위치를 계산.

Publishes:
  /aruco/poses     - 감지된 마커 위치 (로봇 좌표계, PoseArray)
  /aruco/markers   - 마커 ID + 위치 (MarkerArray는 없으므로 PoseArray 사용)
  /aruco/image     - 마커가 그려진 디버그 이미지
  /tf              - 각 마커의 TF (world → aruco_N)

Subscribes:
  /camera/color/image_raw
  /camera/depth/image_raw
  /camera/camera_info
"""

import os
import struct

import cv2
import numpy as np
import rclpy
import yaml
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import PoseArray, Pose, PoseStamped, TransformStamped
from std_msgs.msg import Header
from tf2_ros import TransformBroadcaster


class ArucoDetectorNode(Node):
    def __init__(self):
        super().__init__("aruco_detector_node")

        # Parameters
        self.declare_parameter("marker_size", 0.03)  # 30mm
        self.declare_parameter("intrinsics_file", "")
        self.declare_parameter("hand_eye_file", "")
        self.declare_parameter("aruco_dict", "DICT_4X4_50")

        self.marker_size = self.get_parameter("marker_size").value
        intrinsics_file = self.get_parameter("intrinsics_file").value
        hand_eye_file = self.get_parameter("hand_eye_file").value
        dict_name = self.get_parameter("aruco_dict").value

        # ArUco setup
        aruco_dict_id = getattr(cv2.aruco, dict_name, cv2.aruco.DICT_4X4_50)
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(aruco_dict_id)
        self.aruco_params = cv2.aruco.DetectorParameters()
        self.aruco_detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.aruco_params)

        # Camera intrinsics
        self.camera_matrix = None
        self.dist_coeffs = None
        if intrinsics_file and os.path.exists(intrinsics_file):
            self._load_intrinsics(intrinsics_file)
            self.get_logger().info(f"Loaded intrinsics: fx={self.camera_matrix[0,0]:.1f}")

        # Hand-eye calibration (cam → robot)
        self.R_cam2robot = None
        self.t_cam2robot = None
        if hand_eye_file and os.path.exists(hand_eye_file):
            self._load_hand_eye(hand_eye_file)
            self.get_logger().info("Loaded hand-eye calibration")

        # Subscribers
        self.rgb_sub = self.create_subscription(
            Image, "/camera/color/image_raw", self._rgb_callback, 5
        )
        self.depth_sub = self.create_subscription(
            Image, "/camera/depth/image_raw", self._depth_callback, 5
        )
        self.info_sub = self.create_subscription(
            CameraInfo, "/camera/camera_info", self._info_callback, 5
        )

        # Publishers
        self.poses_pub = self.create_publisher(PoseArray, "/aruco/poses", 5)
        self.debug_pub = self.create_publisher(Image, "/aruco/image", 5)
        self.tf_broadcaster = TransformBroadcaster(self)

        # State
        self.latest_rgb = None
        self.latest_depth = None

        # Detection timer: 10 Hz
        self.timer = self.create_timer(0.1, self._detect)

        self.get_logger().info(
            f"ArUco detector started (dict={dict_name}, marker_size={self.marker_size*100:.0f}cm)"
        )

    def _load_intrinsics(self, path):
        with open(path) as f:
            data = yaml.safe_load(f)
        self.camera_matrix = np.array([
            [data["fx"], 0, data["cx"]],
            [0, data["fy"], data["cy"]],
            [0, 0, 1],
        ], dtype=np.float64)
        self.dist_coeffs = np.array(data.get("dist_coeffs", [0]*5), dtype=np.float64)

    def _load_hand_eye(self, path):
        with open(path) as f:
            data = yaml.safe_load(f)
        self.R_cam2robot = np.array(data["R"], dtype=np.float64)
        self.t_cam2robot = np.array(data["t"], dtype=np.float64)
        self.get_logger().info(
            f"Hand-eye RMSE: {data.get('rmse_mm', '?')} mm, samples: {data.get('num_samples', '?')}"
        )

    def _rgb_callback(self, msg):
        self.latest_rgb = np.frombuffer(msg.data, dtype=np.uint8).reshape(
            msg.height, msg.width, 3
        )

    def _depth_callback(self, msg):
        self.latest_depth = np.frombuffer(msg.data, dtype=np.uint16).reshape(
            msg.height, msg.width
        )

    def _info_callback(self, msg):
        if self.camera_matrix is None:
            self.camera_matrix = np.array(msg.k, dtype=np.float64).reshape(3, 3)
            self.dist_coeffs = np.array(msg.d, dtype=np.float64) if msg.d else np.zeros(5)
            self.get_logger().info("Got camera intrinsics from CameraInfo topic")

    def _pixel_to_cam3d(self, u, v, depth_mm):
        """2D 픽셀 + depth(mm) → 3D 카메라 좌표 (m)"""
        if self.camera_matrix is None:
            return None
        fx = self.camera_matrix[0, 0]
        fy = self.camera_matrix[1, 1]
        cx = self.camera_matrix[0, 2]
        cy = self.camera_matrix[1, 2]
        z = depth_mm / 1000.0
        x = (u - cx) * z / fx
        y = (v - cy) * z / fy
        return np.array([x, y, z])

    def _cam_to_robot(self, point_cam):
        """카메라 좌표 → 로봇 좌표"""
        if self.R_cam2robot is None:
            return point_cam
        return self.R_cam2robot @ point_cam + self.t_cam2robot

    def _get_depth_at(self, u, v, radius=3):
        """depth 맵에서 (u,v) 근처 중앙값 추출"""
        if self.latest_depth is None:
            return 0
        h, w = self.latest_depth.shape
        u, v = int(u), int(v)
        y0 = max(0, v - radius)
        y1 = min(h, v + radius + 1)
        x0 = max(0, u - radius)
        x1 = min(w, u + radius + 1)
        patch = self.latest_depth[y0:y1, x0:x1]
        valid = patch[patch > 0]
        if len(valid) == 0:
            return 0
        return int(np.median(valid))

    def _detect(self):
        if self.latest_rgb is None or self.camera_matrix is None:
            return

        frame = self.latest_rgb.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        corners, ids, rejected = self.aruco_detector.detectMarkers(gray)

        if ids is None or len(ids) == 0:
            # Publish debug image even without detections
            self._publish_debug_image(frame)
            return

        # Draw markers
        cv2.aruco.drawDetectedMarkers(frame, corners, ids)

        pose_array = PoseArray()
        pose_array.header = Header(
            stamp=self.get_clock().now().to_msg(), frame_id="world"
        )

        now = self.get_clock().now().to_msg()

        for i, marker_id in enumerate(ids.flatten()):
            corner = corners[i][0]  # 4 corner points

            # Marker center in pixels
            center = corner.mean(axis=0)
            cu, cv_coord = center[0], center[1]

            # Get depth
            depth_mm = self._get_depth_at(cu, cv_coord)
            if depth_mm <= 0:
                # Fallback: use solvePnP for distance
                obj_points = np.array([
                    [-self.marker_size/2,  self.marker_size/2, 0],
                    [ self.marker_size/2,  self.marker_size/2, 0],
                    [ self.marker_size/2, -self.marker_size/2, 0],
                    [-self.marker_size/2, -self.marker_size/2, 0],
                ], dtype=np.float64)
                ok, rvec, tvec = cv2.solvePnP(
                    obj_points, corner, self.camera_matrix, self.dist_coeffs
                )
                if not ok:
                    continue
                point_cam = tvec.flatten()
            else:
                point_cam = self._pixel_to_cam3d(cu, cv_coord, depth_mm)
                if point_cam is None:
                    continue

            # Transform to robot frame
            point_robot = self._cam_to_robot(point_cam)

            # Create pose
            pose = Pose()
            pose.position.x = float(point_robot[0])
            pose.position.y = float(point_robot[1])
            pose.position.z = float(point_robot[2])
            pose.orientation.w = 1.0  # identity quaternion
            pose_array.poses.append(pose)

            # Broadcast TF
            t = TransformStamped()
            t.header.stamp = now
            t.header.frame_id = "world"
            t.child_frame_id = f"aruco_{marker_id}"
            t.transform.translation.x = float(point_robot[0])
            t.transform.translation.y = float(point_robot[1])
            t.transform.translation.z = float(point_robot[2])
            t.transform.rotation.w = 1.0
            self.tf_broadcaster.sendTransform(t)

            # Draw info on frame
            cv2.putText(
                frame,
                f"ID:{marker_id} ({point_robot[0]:.3f},{point_robot[1]:.3f},{point_robot[2]:.3f})",
                (int(cu), int(cv_coord) - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2,
            )

        self.poses_pub.publish(pose_array)
        self._publish_debug_image(frame)

    def _publish_debug_image(self, frame):
        msg = Image()
        msg.header = Header(
            stamp=self.get_clock().now().to_msg(), frame_id="camera_link"
        )
        msg.height, msg.width = frame.shape[:2]
        msg.encoding = "bgr8"
        msg.step = msg.width * 3
        msg.data = frame.tobytes()
        self.debug_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = ArucoDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
