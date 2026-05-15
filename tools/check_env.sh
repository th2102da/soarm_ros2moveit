#!/usr/bin/env bash
# SO-ARM101 ROS2 환경 점검 — 한 번에 모든 항목 확인
# 사용: ./tools/check_env.sh
set -o pipefail

ok()   { printf "  ✓ %s\n" "$1"; }
fail() { printf "  ✗ %s\n" "$1"; FAILED=1; }
info() { printf "  ● %s\n" "$1"; }

FAILED=0

echo "== OS =="
. /etc/os-release
[[ "$VERSION_ID" == "24.04" ]] && ok "Ubuntu 24.04 ($VERSION_CODENAME)" || fail "Ubuntu $VERSION_ID (24.04 권장)"

echo "== ROS2 =="
if [[ -f /opt/ros/jazzy/setup.bash ]]; then
    ok "ROS2 Jazzy 설치됨"
    # shellcheck disable=SC1091
    source /opt/ros/jazzy/setup.bash
    [[ "${ROS_DISTRO:-}" == "jazzy" ]] && ok "ROS_DISTRO=jazzy 활성화" || fail "ROS_DISTRO 미설정"
else
    fail "ROS2 Jazzy 미설치 (/opt/ros/jazzy 없음)"
fi

echo "== MoveIt2 / ros2_control =="
PKGS=$(ros2 pkg list 2>/dev/null)
for pkg in moveit moveit_planners_ompl controller_manager joint_trajectory_controller; do
    if printf '%s\n' "$PKGS" | grep -qx "$pkg"; then
        ok "$pkg"
    else
        fail "$pkg 미설치 — sudo apt install ros-jazzy-${pkg//_/-}"
    fi
done

echo "== Gazebo Harmonic (선택) =="
if printf '%s\n' "$PKGS" | grep -qx "gz_ros2_control"; then
    ok "gz_ros2_control"
else
    info "gz_ros2_control 없음 (Gazebo 시뮬 안 쓸 거면 무시)"
fi

echo "== 하드웨어 권한 =="
groups | grep -qw dialout && ok "dialout 그룹 ($USER) — /dev/ttyACM* 접근 가능" || fail "dialout 미가입: sudo usermod -aG dialout $USER (재로그인 필요)"
groups | grep -qw video && ok "video 그룹 — 카메라 접근 가능" || info "video 그룹 없음 (HP60C 카메라 안 쓸 거면 무시)"
[[ -e /dev/ttyACM0 ]] && ok "/dev/ttyACM0 존재" || info "/dev/ttyACM0 없음 (지금 로봇 미연결이면 정상)"

echo "== 워크스페이스 =="
WS="$(cd "$(dirname "$0")/.." && pwd)/ws"
[[ -d "$WS/src" ]] && ok "ws/src 존재: $WS/src" || fail "ws/src 없음"

echo
[[ $FAILED -eq 0 ]] && echo "결과: 모두 통과" || { echo "결과: 일부 실패 — 위 ✗ 항목 확인"; exit 1; }
