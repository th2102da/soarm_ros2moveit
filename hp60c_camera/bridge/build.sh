#!/usr/bin/env bash
# HP60C shm_bridge 빌드 스크립트
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [[ -z "${HP60C_SDK_DIR:-}" ]]; then
    cat >&2 <<EOF
HP60C_SDK_DIR 환경변수가 비어있습니다.

예시:
  export HP60C_SDK_DIR=\$HOME/hp60c_sdk/linux_ros/linux
  $0
EOF
    exit 1
fi

mkdir -p "$SCRIPT_DIR/build"
cd "$SCRIPT_DIR/build"
cmake -DHP60C_SDK_DIR="$HP60C_SDK_DIR" ..
make -j"$(nproc)"
echo
echo "빌드 완료: $SCRIPT_DIR/build/shm_bridge"
