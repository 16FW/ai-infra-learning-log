#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
uptime; nproc
cp app/main.py /tmp/main.py.bak
trap 'cp /tmp/main.py.bak app/main.py' EXIT     # 중간에 실패해도 원복

echo "== 처음 빌드 =="
docker build -q -f Dockerfile.v2 -t lesson03:v2 .
docker build -q -f Dockerfile.multistage -t lesson03:ms .

echo "== 크기 =="
docker images lesson03 --format "table {{.Tag}}\t{{.Size}}"
echo "== history v2 =="; docker history lesson03:v2
echo "== history ms =="; docker history lesson03:ms

echo "== main.py 한 줄 수정 후 재빌드 시간 =="
echo "# change $(date +%s)" >> app/main.py
s=$(date +%s.%N); docker build -q -f Dockerfile.v2 -t lesson03:v2 . >/dev/null; e=$(date +%s.%N)
echo "v2: $(awk "BEGIN{printf \"%.1f\", $e-$s}")s"
s=$(date +%s.%N); docker build -q -f Dockerfile.multistage -t lesson03:ms . >/dev/null; e=$(date +%s.%N)
echo "multistage: $(awk "BEGIN{printf \"%.1f\", $e-$s}")s"
