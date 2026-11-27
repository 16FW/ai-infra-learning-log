#!/usr/bin/env bash
cd "$(dirname "$0")"
rm -rf data data2
mkdir -p data data2

docker run --rm -v "$PWD/data":/data lesson05:counter
docker run --rm -v "$PWD/data":/data lesson05:counter
echo "-- TODO1 호스트에서 보이는지, 소유자:"
ls -l data/
id

echo "-- TODO2 호스트 계정으로 수정:"
echo 100 > data/count.txt; echo "  (exit=$?)"

echo "-- TODO3 내 UID로 컨테이너 실행:"
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD/data2":/data lesson05:counter
ls -l data2/
echo 100 > data2/count.txt; echo "  (수정 exit=$?)"

echo "-- TODO4 :ro 마운트에서 쓰기 시도:"
docker run --rm -v "$PWD/data":/data:ro lesson05:counter; echo "  (exit=$?)"
