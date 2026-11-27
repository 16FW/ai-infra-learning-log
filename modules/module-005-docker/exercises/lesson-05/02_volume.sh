#!/usr/bin/env bash
docker volume rm cnt >/dev/null 2>&1
docker volume create cnt

echo "-- TODO4 볼륨 사용, --rm으로 3번:"
for i in 1 2 3; do docker run --rm -v cnt:/data lesson05:counter; done
docker volume ls
echo "-- TODO5 inspect:"
docker volume inspect cnt

echo "-- TODO6 볼륨 없이 --rm으로 3번:"
for i in 1 2 3; do docker run --rm lesson05:counter; done

docker volume rm cnt
