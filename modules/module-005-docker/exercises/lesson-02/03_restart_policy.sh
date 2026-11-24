#!/usr/bin/env bash
docker rm -f crash >/dev/null 2>&1
T0=$(date -Iseconds)
docker run -d --restart=on-failure:3 --name crash alpine sh -c "exit 1" >/dev/null
sleep 10
docker inspect -f 'RestartCount={{.RestartCount}} Status={{.State.Status}} Exit={{.State.ExitCode}}' crash
# 재시작 간격: start 이벤트 시각(ns) 차이를 본다
docker events --since "$T0" --until "$(date -Iseconds)" \
  --filter container=crash --filter event=start --format '{{.TimeNano}}'
docker rm -f crash
