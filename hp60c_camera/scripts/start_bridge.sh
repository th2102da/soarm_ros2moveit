#!/usr/bin/env bash
# HP60C shm_bridge 실행
#
# 환경변수:
#   HP60C_SDK_DIR        SDK 루트 (필수). 예) ~/hp60c_sdk/linux_ros/linux
#   HP60C_CONFIG_DIR     카메라 설정 파일 디렉토리 (선택)
#                        기본값: $HP60C_SDK_DIR/configurationfiles
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PKG_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BRIDGE="$PKG_ROOT/bridge/build/shm_bridge"

if [[ -z "${HP60C_SDK_DIR:-}" ]]; then
    echo "HP60C_SDK_DIR 환경변수를 설정하세요." >&2
    exit 1
fi

if [[ ! -x "$BRIDGE" ]]; then
    echo "shm_bridge 바이너리가 없습니다. 먼저 빌드하세요:" >&2
    echo "  cd $PKG_ROOT/bridge && ./build.sh" >&2
    exit 1
fi

CONFIG_DIR="${HP60C_CONFIG_DIR:-$HP60C_SDK_DIR/configurationfiles}"
SDK_LIB="$HP60C_SDK_DIR/libs/lib/x86_64-linux-gnu"

echo "[start_bridge] SDK lib   : $SDK_LIB"
echo "[start_bridge] Config dir: $CONFIG_DIR"
echo "[start_bridge] Ctrl+C 로 종료"
echo

exec env LD_LIBRARY_PATH="$SDK_LIB:${LD_LIBRARY_PATH:-}" \
        "$BRIDGE" "$CONFIG_DIR"
