#!/usr/bin/env python3
"""ROS2 Hand-Eye 캘리브레이션 노드

ArUco 마커를 그리퍼에 부착하고, 여러 포즈에서 캡처하여
카메라→로봇 변환(R, t)을 계산.

Usage:
  1. MoveIt demo를 mock 또는 real로 실행
  2. 이 노드 실행:
     ros2 run soarm101_pick_place calibrate_hand_eye_node.py

  3. 로봇을 다양한 자세로 움직인 후 's' 키로 샘플 캡처
  4. 충분한 샘플(10~20개) 모은 후 'c'로 캘리브레이션 계산
  5. 결과가 config/cam_to_robot.yaml에 저장됨
"""

import os

import cv2
import numpy as np
import rclpy
import yaml
from rclpy.node import Node
from sensor_msgs.msg import Image, JointState


class CalibrateHandEyeNode(Node):
    def __init__(self):
        super().__init__("calibrate_hand_eye_node")

        self.declare_parameter("marker_size", 0.03)
        self.declare_parameter("intrinsics_file", "")
        self.declare_parameter("output_file", "cam_to_robot.yaml")
        self.declare_parameter("marker_id", 0)

        self.marker_size = self.get_parameter("marker_size").value
        self.target_id = self.get_parameter("marker_id").value
        output = self.get_parameter("output_file").value

        # Load intrinsics
        intrinsics_file = self.get_parameter("intrinsics_file").value
        self.camera_matrix = None
        self.dist_coeffs = None
        if intrinsics_file and os.path.exists(intrinsics_file):
            with open(intrinsics_file) as f:
                data = yaml.safe_load(f)
            self.camera_matrix = np.array([
                [data["fx"], 0, data["cx"]],
                [0, data["fy"], data["cy"]],
                [0, 0, 1],
            ])
            self.dist_coeffs = np.array(data.get("dist_coeffs", [0]*5))

        # ArUco
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        self.aruco_detector = cv2.aruco.ArucoDetector(
            self.aruco_dict, cv2.aruco.DetectorParameters()
        )

        # Subscribers
        self.rgb_sub = self.create_subscription(
            Image, "/camera/color/image_raw", self._rgb_cb, 5
        )
        self.joint_sub = self.create_subscription(
            JointState, "/joint_states", self._joint_cb, 5
        )

        self.latest_rgb = None
        self.latest_joints = None
        self.cam_points = []
        self.robot_points = []

        self.output_file = output

        # Display timer
        self.timer = self.create_timer(0.1, self._display)

        self.get_logger().info(
            "Hand-eye calibration node started.\n"
            "  's' = capture sample\n"
            "  'c' = compute calibration\n"
            "  'q' = quit"
        )

    def _rgb_cb(self, msg):
        self.latest_rgb = np.frombuffer(msg.data, dtype=np.uint8).reshape(
            msg.height, msg.width, 3
        )

    def _joint_cb(self, msg):
        self.latest_joints = dict(zip(msg.name, msg.position))

    def _detect_marker(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = self.aruco_detector.detectMarkers(gray)

        if ids is None:
            return None, None, frame

        for i, mid in enumerate(ids.flatten()):
            if mid == self.target_id:
                obj_pts = np.array([
                    [-self.marker_size/2,  self.marker_size/2, 0],
                    [ self.marker_size/2,  self.marker_size/2, 0],
                    [ self.marker_size/2, -self.marker_size/2, 0],
                    [-self.marker_size/2, -self.marker_size/2, 0],
                ], dtype=np.float64)

                ok, rvec, tvec = cv2.solvePnP(
                    obj_pts, corners[i][0], self.camera_matrix, self.dist_coeffs
                )
                if ok:
                    cv2.aruco.drawDetectedMarkers(frame, [corners[i]], np.array([[mid]]))
                    cv2.drawFrameAxes(
                        frame, self.camera_matrix, self.dist_coeffs,
                        rvec, tvec, self.marker_size * 0.5
                    )
                    return tvec.flatten(), rvec.flatten(), frame

        return None, None, frame

    def _display(self):
        if self.latest_rgb is None:
            return

        frame = self.latest_rgb.copy()
        tvec, rvec, frame = self._detect_marker(frame)

        # Status text
        status = f"Samples: {len(self.cam_points)}"
        if tvec is not None:
            status += f" | Marker: ({tvec[0]:.3f}, {tvec[1]:.3f}, {tvec[2]:.3f})"
        cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, "s=capture  c=calibrate  q=quit", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        cv2.imshow("Hand-Eye Calibration", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("s"):
            self._capture_sample(tvec)
        elif key == ord("c"):
            self._compute_calibration()
        elif key == ord("q"):
            cv2.destroyAllWindows()
            raise SystemExit

    def _capture_sample(self, tvec):
        if tvec is None:
            self.get_logger().warn("No marker detected!")
            return
        if self.latest_joints is None:
            self.get_logger().warn("No joint states!")
            return

        # Camera point (from solvePnP)
        self.cam_points.append(tvec.copy())

        # Robot point (from FK via joint_states — for now just save joints)
        # In a real setup, you'd compute FK here. For now, we need the user
        # to manually record the gripper position.
        # TODO: integrate with MoveIt FK service

        self.get_logger().info(
            f"Sample {len(self.cam_points)}: cam=({tvec[0]:.4f}, {tvec[1]:.4f}, {tvec[2]:.4f})"
        )
        self.get_logger().info(f"  joints: {self.latest_joints}")

    def _compute_calibration(self):
        n = len(self.cam_points)
        if n < 4:
            self.get_logger().error(f"Need at least 4 samples, have {n}")
            return

        cam_pts = np.array(self.cam_points)
        # For now, this is a placeholder. Full implementation needs FK-computed robot points.
        self.get_logger().info(f"Captured {n} camera points. Full calibration requires FK robot points.")
        self.get_logger().info("Use the existing cam_to_robot.yaml for now, or implement FK integration.")


def main(args=None):
    rclpy.init(args=args)
    node = CalibrateHandEyeNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
