cmake_minimum_required(VERSION 3.10)
project(hp60c_shm_bridge CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# HP60C SDK 경로 — 환경변수 또는 -DHP60C_SDK_DIR=... 으로 지정
# SDK 루트는 보통 <download>/linux_ros/linux 디렉토리이며,
# 그 아래 libs/include, libs/lib/x86_64-linux-gnu 가 있어야 한다.
if(NOT DEFINED HP60C_SDK_DIR)
    set(HP60C_SDK_DIR "$ENV{HP60C_SDK_DIR}")
endif()
if(NOT HP60C_SDK_DIR)
    message(FATAL_ERROR
        "HP60C SDK 경로가 설정되지 않았습니다. 둘 중 하나를 사용하세요:\n"
        "  export HP60C_SDK_DIR=/path/to/hp60c_sdk/linux_ros/linux\n"
        "  cmake -DHP60C_SDK_DIR=/path/to/hp60c_sdk/linux_ros/linux ..")
endif()

set(SDK_INC "${HP60C_SDK_DIR}/libs/include")
set(SDK_LIB "${HP60C_SDK_DIR}/libs/lib/x86_64-linux-gnu")

if(NOT EXISTS "${SDK_INC}/as_camera_sdk_api.h")
    message(FATAL_ERROR "SDK 헤더를 찾을 수 없습니다: ${SDK_INC}/as_camera_sdk_api.h")
endif()
if(NOT EXISTS "${SDK_LIB}/libAngstrongCameraSdk.so")
    message(FATAL_ERROR "SDK 라이브러리를 찾을 수 없습니다: ${SDK_LIB}/libAngstrongCameraSdk.so")
endif()

add_executable(shm_bridge shm_bridge.cpp)
target_include_directories(shm_bridge PRIVATE ${SDK_INC})
target_link_directories(shm_bridge PRIVATE ${SDK_LIB})
target_link_libraries(shm_bridge
    AngstrongCameraSdk
    pthread
    rt
)

# 런타임에 libAngstrongCameraSdk.so 를 찾도록 RPATH 설정
set_target_properties(shm_bridge PROPERTIES
    BUILD_RPATH   "${SDK_LIB}"
    INSTALL_RPATH "${SDK_LIB}"
)
