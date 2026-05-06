#!/usr/bin/env python3
"""카메라 브릿지 노드: 공유메모리(shm_bridge) → ROS2 토픽

shm_bridge가 /dev/shm/hp60c_frames에 RGB+Depth를 쓰면,
이 노드가 읽어서 ROS2 Image/CameraInfo로 퍼블리시.

Usage:
  # 터미널 1: shm_bridge 실행
  sudo bash ~/soarm_project/start_camera.sh

  # 터미널 2: 이 노드 실행
  ros2 run soarm101_pick_place camera_bridge_node.py
"""

import struct
import mmap
import os

import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from std_msgs.msg import Header
import yaml


SHM_NAME = "/dev/shm/hp60c_frames"
HEADER_SIZE = 64
MAX_RGB_SIZE = 1920 * 1080 * 3
MAGIC = 0x48503630


class CameraBridgeNode(Node):
    def __init__(self):
        super().__init__("camera_bridge_node")

        # Publishers
        self.rgb_pub = self.create_publisher(Image, "/camera/color/image_raw", 5)
        self.depth_pub = self.create_publisher(Image, "/camera/depth/image_raw", 5)
        self.info_pub = self.create_publisher(CameraInfo, "/camera/camera_info", 5)

        # Load camera intrinsics
        config_path = self.declare_parameter(
            "intrinsics_file", ""
        ).get_parameter_value().string_value

        if config_path and os.path.exists(config_path):
            self.camera_info = self._load_intrinsics(config_path)
            self.get_logger().info(f"Loaded intrinsics from {config_path}")
        else:
            self.camera_info = self._default_intrinsics()
            self.get_logger().warn("Using default intrinsics (no file specified)")

        # Open shared memory
        self.shm_fd = None
        self.shm_mm = None
        self._open_shm()

        # Timer: 15 Hz
        self.timer = self.create_timer(1.0 / 15.0, self._timer_callback)
        self.frame_count = 0
        self.last_frame_id = 0

        self.get_logger().info("Camera bridge node started (15 Hz)")

    def _open_shm(self):
        if not os.path.exists(SHM_NAME):
            self.get_logger().error(
                f"{SHM_NAME} not found. Run shm_bridge first!"
            )
            return

        self.shm_fd = os.open(SHM_NAME, os.O_RDONLY)
        file_size = os.fstat(self.shm_fd).st_size
        self.shm_mm = mmap.mmap(self.shm_fd, file_size, access=mmap.ACCESS_READ)
        self.get_logger().info(f"Opened {SHM_NAME} ({file_size} bytes)")

    def _timer_callback(self):
        if self.shm_mm is None:
            self._open_shm()
            if self.shm_mm is None:
                return

        # Read header
        header_data = self.shm_mm[:HEADER_SIZE]
        (
            magic, rgb_w, rgb_h, rgb_size,
            depth_w, depth_h, depth_size, _pad,
            frame_id, timestamp_us,
            rgb_ready, depth_ready,
        ) = struct.unpack("<IIIIIIII QQ II", header_data)

        if magic != MAGIC:
            return

        # Skip if same frame
        if frame_id == self.last_frame_id:
            return
        self.last_frame_id = frame_id

        now = self.get_clock().now().to_msg()
        header = Header(stamp=now, frame_id="camera_link")

        # Publish RGB
        if rgb_ready and rgb_size > 0:
            rgb_offset = HEADER_SIZE
            rgb_bytes = self.shm_mm[rgb_offset:rgb_offset + rgb_size]
            rgb_msg = Image()
            rgb_msg.header = header
            rgb_msg.height = rgb_h
            rgb_msg.width = rgb_w
            rgb_msg.encoding = "bgr8"
            rgb_msg.step = rgb_w * 3
            rgb_msg.data = rgb_bytes
            self.rgb_pub.publish(rgb_msg)

        # Publish Depth
        if depth_ready and depth_size > 0:
            depth_offset = HEADER_SIZE + MAX_RGB_SIZE
            depth_bytes = self.shm_mm[depth_offset:depth_offset + depth_size]
            depth_msg = Image()
            depth_msg.header = header
            depth_msg.height = depth_h
            depth_msg.width = depth_w
            depth_msg.encoding = "16UC1"  # uint16 mm
            depth_msg.step = depth_w * 2
            depth_msg.data = depth_bytes
            self.depth_pub.publish(depth_msg)

        # Publish CameraInfo
        self.camera_info.header = header
        self.info_pub.publish(self.camera_info)

        self.frame_count += 1
        if self.frame_count % 150 == 0:
            self.get_logger().info(f"Published {self.frame_count} frames")

    def _load_intrinsics(self, path):
        with open(path) as f:
            data = yaml.safe_load(f)

        info = CameraInfo()
        info.width = data.get("image_width", 640)
        info.height = data.get("image_height", 480)
        info.distortion_model = "plumb_bob"

        fx = data["fx"]
        fy = data["fy"]
        cx = data["cx"]
        cy = data["cy"]

        info.k = [fx, 0.0, cx, 0.0, fy, cy, 0.0, 0.0, 1.0]
        info.p = [fx, 0.0, cx, 0.0, 0.0, fy, cy, 0.0, 0.0, 0.0, 1.0, 0.0]
        info.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]

        dist = data.get("dist_coeffs", [0.0] * 5)
        info.d = [float(d) for d in dist]

        return info

    def _default_intrinsics(self):
        info = CameraInfo()
        info.width = 640
        info.height = 480
        info.distortion_model = "plumb_bob"
        info.k = [619.7, 0.0, 294.8, 0.0, 622.0, 198.5, 0.0, 0.0, 1.0]
        info.p = [619.7, 0.0, 294.8, 0.0, 0.0, 622.0, 198.5, 0.0, 0.0, 0.0, 1.0, 0.0]
        info.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        info.d = [0.0] * 5
        return info

    def destroy_node(self):
        if self.shm_mm:
            self.shm_mm.close()
        if self.shm_fd:
            os.close(self.shm_fd)
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = CameraBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
