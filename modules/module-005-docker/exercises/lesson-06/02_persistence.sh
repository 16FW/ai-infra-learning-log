#!/usr/bin/env bash
hit() {
  for i in $(seq 1 10); do
    out=$(curl -s -f localhost:8000/hits) && { echo "$out"; return; }
    sleep 1
  done
  echo "FAILED"
}

echo "== 현재 값 =="; hit
docker compose down
docker compose up -d
echo "== TODO 5: down 후 up =="; hit
docker volume ls | grep hitsdata

docker compose down -v
docker compose up -d
echo "== TODO 6: down -v 후 up =="; hit

docker compose down -v
