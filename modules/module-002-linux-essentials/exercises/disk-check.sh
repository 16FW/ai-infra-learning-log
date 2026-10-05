#!/bin/bash
set -euo pipefail

# 1. 인자로 받은 모든 경로를 배열에 저장
PATHS=("$@")

# 2. 인자가 없으면 기본값 '/' 지정
if [ "${#PATHS[@]}" -eq 0 ]; then
    PATHS=("/")
fi

# 3. 배열 안의 모든 경로를 순회하며 디스크 점검
for p in "${PATHS[@]}"; do
    echo "검사할 경로: $p"

    # 경로 존재 여부 검사 (-e)
    if [ ! -e "$p" ]; then
        echo "Error: Path '$p' does not exist." >&2
        continue
    fi

    # 디스크 사용률 계산 (POSIX 표준 df -P 사용)
    USAGE=$(df -P "$p" | tail -1 | awk '{print $5}' | tr -d '%')

    # 판별 및 출력
    if [ "$USAGE" -ge 80 ]; then
        echo "Warning: Disk usage on '$p' is at ${USAGE}% (80% or higher)."
    else
        echo "OK: Disk usage on '$p' is at ${USAGE}%."
    fi
done
