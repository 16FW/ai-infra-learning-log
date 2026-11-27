#!/usr/bin/env bash
cd "$(dirname "$0")"
docker rm -f c1 c2 >/dev/null 2>&1

echo "-- TODO1 c1 첫 실행:"
docker run --name c1 lesson05:counter
echo "-- TODO2 같은 컨테이너 다시 시작:"
docker start -a c1
echo "-- docker diff (쓰기 레이어에 생긴 변경):"
docker diff c1
docker rm c1 >/dev/null

echo "-- TODO3 새 컨테이너 c2:"
docker run --name c2 lesson05:counter
docker rm c2 >/dev/null
