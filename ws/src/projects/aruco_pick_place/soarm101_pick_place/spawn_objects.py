#!/usr/bin/env python3
"""Gazebo에 테이블 + 물체를 스폰하는 노드"""

import subprocess
import sys
import time

import rclpy
from rclpy.node import Node


OBJECTS = [
    # (name, sdf_string)
    ("table", """<?xml version="1.0" ?>
<sdf version="1.8">
  <model name="table">
    <static>true</static>
    <pose>0.15 0 -0.01 0 0 0</pose>
    <link name="link">
      <collision name="collision">
        <geometry><box><size>0.35 0.50 0.02</size></box></geometry>
      </collision>
      <visual name="visual">
        <geometry><box><size>0.35 0.50 0.02</size></box></geometry>
        <material>
          <ambient>0.6 0.4 0.2 1</ambient>
          <diffuse>0.6 0.4 0.2 1</diffuse>
        </material>
      </visual>
    </link>
  </model>
</sdf>"""),

    ("red_cube", """<?xml version="1.0" ?>
<sdf version="1.8">
  <model name="red_cube">
    <pose>0.12 0.05 0.025 0 0 0</pose>
    <link name="link">
      <inertial>
        <mass>0.03</mass>
        <inertia>
          <ixx>0.000005</ixx><iyy>0.000005</iyy><izz>0.000005</izz>
        </inertia>
      </inertial>
      <collision name="collision">
        <geometry><box><size>0.03 0.03 0.03</size></box></geometry>
        <surface>
          <friction><ode><mu>1.0</mu><mu2>1.0</mu2></ode></friction>
        </surface>
      </collision>
      <visual name="visual">
        <geometry><box><size>0.03 0.03 0.03</size></box></geometry>
        <material>
          <ambient>1 0 0 1</ambient>
          <diffuse>1 0 0 1</diffuse>
        </material>
      </visual>
    </link>
  </model>
</sdf>"""),

    ("blue_cylinder", """<?xml version="1.0" ?>
<sdf version="1.8">
  <model name="blue_cylinder">
    <pose>0.15 -0.06 0.025 0 0 0</pose>
    <link name="link">
      <inertial>
        <mass>0.03</mass>
        <inertia>
          <ixx>0.000004</ixx><iyy>0.000004</iyy><izz>0.000003</izz>
        </inertia>
      </inertial>
      <collision name="collision">
        <geometry><cylinder><radius>0.015</radius><length>0.04</length></cylinder></geometry>
        <surface>
          <friction><ode><mu>1.0</mu><mu2>1.0</mu2></ode></friction>
        </surface>
      </collision>
      <visual name="visual">
        <geometry><cylinder><radius>0.015</radius><length>0.04</length></cylinder></geometry>
        <material>
          <ambient>0 0 1 1</ambient>
          <diffuse>0.2 0.2 1 1</diffuse>
        </material>
      </visual>
    </link>
  </model>
</sdf>"""),

    ("green_cube", """<?xml version="1.0" ?>
<sdf version="1.8">
  <model name="green_cube">
    <pose>0.20 0.0 0.02 0 0 0</pose>
    <link name="link">
      <inertial>
        <mass>0.02</mass>
        <inertia>
          <ixx>0.000003</ixx><iyy>0.000003</iyy><izz>0.000003</izz>
        </inertia>
      </inertial>
      <collision name="collision">
        <geometry><box><size>0.025 0.025 0.025</size></box></geometry>
        <surface>
          <friction><ode><mu>1.0</mu><mu2>1.0</mu2></ode></friction>
        </surface>
      </collision>
      <visual name="visual">
        <geometry><box><size>0.025 0.025 0.025</size></box></geometry>
        <material>
          <ambient>0 0.8 0 1</ambient>
          <diffuse>0.1 0.9 0.1 1</diffuse>
        </material>
      </visual>
    </link>
  </model>
</sdf>"""),
]


class SpawnObjects(Node):
    def __init__(self):
        super().__init__("spawn_objects")

    def spawn_all(self):
        for name, sdf in OBJECTS:
            self.get_logger().info(f"Spawning '{name}'...")
            sdf_oneline = sdf.replace("\n", " ").replace('"', '\\"')
            try:
                result = subprocess.run(
                    [
                        "gz", "service",
                        "-s", "/world/empty/create",
                        "--reqtype", "gz.msgs.EntityFactory",
                        "--reptype", "gz.msgs.Boolean",
                        "--timeout", "5000",
                        "--req", f'sdf: "{sdf_oneline}"',
                    ],
                    capture_output=True, text=True, timeout=10,
                )
                if "true" in result.stdout.lower() or result.returncode == 0:
                    self.get_logger().info(f"  '{name}' spawned OK")
                else:
                    self.get_logger().warn(f"  '{name}': {result.stderr.strip()}")
            except Exception as e:
                self.get_logger().warn(f"  '{name}' failed: {e}")
            time.sleep(0.5)


def main(args=None):
    rclpy.init(args=args)
    node = SpawnObjects()
    node.spawn_all()
    node.get_logger().info("All objects spawned. Shutting down.")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
