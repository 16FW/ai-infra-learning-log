#!/usr/bin/env bash
docker rm -f t1 >/dev/null 2>&1
docker run -d --name t1 alpine sleep 300 >/dev/null
sleep 2
T0=$(date -Iseconds)
time docker stop t1 >/dev/null
docker inspect -f 'exit={{.State.ExitCode}} StopTimeout={{.Config.StopTimeout}}' t1
docker events --since "$T0" --until "$(date -Iseconds)" \
  --filter container=t1 --filter event=kill \
  --format '{{.TimeNano}} signal={{.Actor.Attributes.signal}}'
docker rm t1
