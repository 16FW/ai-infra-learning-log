#!/usr/bin/env bash
cd "$(dirname "$0")"
uptime; nproc

docker rm -f burn burn2 >/dev/null 2>&1
docker run -d --name burn --cpus=0.5 --memory=200m \
  -v "$PWD":/work python:3.12-slim python /work/cpuburn.py >/dev/null
sleep 5
echo "== 로그(os.cpu_count) =="; docker logs burn | head -1
echo "== cpu.max =="; docker exec burn cat /sys/fs/cgroup/cpu.max
echo "== stats (제한 있음) =="; docker stats --no-stream burn
echo "== throttling =="; docker exec burn grep -E "nr_throttled|throttled_usec" /sys/fs/cgroup/cpu.stat
echo "== 상태(안 죽었나) =="; docker inspect -f '{{.State.Status}} OOMKilled={{.State.OOMKilled}}' burn

docker run -d --name burn2 -v "$PWD":/work python:3.12-slim python /work/cpuburn.py >/dev/null
sleep 5
echo "== stats (제한 없음) =="; docker stats --no-stream burn2
echo "== cpu.max (제한 없음) =="; docker exec burn2 cat /sys/fs/cgroup/cpu.max
docker rm -f burn burn2
