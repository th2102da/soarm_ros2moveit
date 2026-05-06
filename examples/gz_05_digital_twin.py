#!/usr/bin/env python3
"""디지털 트윈: 실제 SO-ARM101 → Gazebo 미러링

feetech-servo-sdk로 실제 서보 위치를 읽고,
Gazebo의 joint_trajectory_controller에 실시간 전달.

실행 순서:
  1) Gazebo 시작:
     ros2 launch so_arm_gz so_arm_gz_bringup.launch.py arm_id:=so_arm101 launch_rviz:=false
  2) 물체 스폰:
     ros2 run soarm101_pick_place spawn_objects.py
  3) 이 스크립트:
     python3 ~/soarm101_ros2_moveit/examples/gz_05_digital_twin.py
"""

import math
import sys
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray

from scservo_sdk import PortHandler, PacketHandler, COMM_SUCCESS

# STS3215 레지스터
ADDR_TORQUE_ENABLE = 40
ADDR_PRESENT_POSITION = 56
BAUDRATE = 1_000_000
PROTOCOL_VERSION = 0  # SCS protocol

SERVO_IDS = [1, 2, 3, 4, 5, 6]  # shoulder_pan ~ gripper
JOINT_NAMES = [
    "shoulder_pan_joint",
    "shoulder_lift_joint",
    "elbow_flex_joint",
    "wrist_flex_joint",
    "wrist_roll_joint",
]
OFFSETS = [2307, 1555, 2412, 833, 990]  # 현재 자세 = Gazebo zero 기준


def raw_to_rad(raw, offset):
    return (raw - offset) * (2 * math.pi / 4096)


class DigitalTwin(Node):
    def __init__(self):
        super().__init__("digital_twin")

        self.declare_parameter("usb_port", "/dev/ttyACM0")
        port = self.get_parameter("usb_port").value

        # forward_position_controller publisher
        self.cmd_pub = self.create_publisher(
            Float64MultiArray,
            "/forward_position_controller/commands",
            10,
        )

        # Feetech serial setup
        self.get_logger().info(f"Opening serial port: {port}")
        self.port_handler = PortHandler(port)
        self.packet_handler = PacketHandler(PROTOCOL_VERSION)

        if not self.port_handler.openPort():
            self.get_logger().fatal(f"Cannot open port {port}")
            sys.exit(1)
        self.port_handler.setBaudRate(BAUDRATE)
        self.get_logger().info(f"Port opened at {BAUDRATE} baud")

        # 토크 비활성화 — 손으로 자유롭게 움직일 수 있게
        self.get_logger().info("Disabling torque on all servos...")
        for sid in SERVO_IDS:
            self.packet_handler.write1ByteTxRx(self.port_handler, sid, ADDR_TORQUE_ENABLE, 0)
        self.get_logger().info("Torque OFF — move the arm by hand!")

        # 20Hz
        self.timer = self.create_timer(1.0 / 20.0, self._tick)
        self.frame_count = 0

        self.get_logger().info("=== Digital Twin Ready ===")
        self.get_logger().info("Gazebo robot will follow your hand movements!")

    def _read_position(self, servo_id):
        pos, result, error = self.packet_handler.read2ByteTxRx(
            self.port_handler, servo_id, ADDR_PRESENT_POSITION
        )
        if result != COMM_SUCCESS:
            return None
        return pos

    def _tick(self):
        rads = []
        for i, sid in enumerate(SERVO_IDS[:5]):  # arm joints only
            raw = self._read_position(sid)
            if raw is None:
                return  # skip this frame
            rad = raw_to_rad(raw, OFFSETS[i])
            rads.append(rad)

        # Publish to forward_position_controller
        msg = Float64MultiArray()
        msg.data = rads
        self.cmd_pub.publish(msg)

        self.frame_count += 1
        if self.frame_count % 100 == 0:
            pos_str = " ".join(f"{r:+.2f}" for r in rads)
            self.get_logger().info(f"[{self.frame_count}] {pos_str}")

    def destroy_node(self):
        self.get_logger().info("Closing serial port...")
        self.port_handler.closePort()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = DigitalTwin()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
