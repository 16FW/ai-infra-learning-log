#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

docker build -q -f Dockerfile.layers -t layers-split .
docker build -q -f Dockerfile.merged -t layers-merged .

echo "== 레이어별 크기 (분리) =="
docker history --format '{{.Size}}\t{{.CreatedBy}}' layers-split
echo "== 레이어별 크기 (합침) =="
docker history --format '{{.Size}}\t{{.CreatedBy}}' layers-merged

echo "== RootFS.Layers 개수 =="
for t in layers-split layers-merged; do
  echo "$t: $(docker image inspect $t -f '{{len .RootFS.Layers}}')"
done

echo "== 이미지 크기 (MiB) =="
for t in python:3.12-slim layers-split layers-merged; do
  b=$(docker image inspect $t -f '{{.Size}}')
  echo "$t: $((b / 1024 / 1024)) MiB"
done
