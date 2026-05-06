cmake_minimum_required(VERSION 3.22)
project(soarm101_pick_place)

find_package(ament_cmake REQUIRED)

install(DIRECTORY config launch rviz
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
  soarm101_pick_place/camera_bridge_node.py
  soarm101_pick_place/aruco_detector_node.py
  soarm101_pick_place/pick_place_node.py
  soarm101_pick_place/calibrate_hand_eye_node.py
  soarm101_pick_place/spawn_objects.py
  DESTINATION lib/${PROJECT_NAME}
)

install(PROGRAMS
  ${CMAKE_CURRENT_SOURCE_DIR}/../../../examples/gz_05_digital_twin.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
