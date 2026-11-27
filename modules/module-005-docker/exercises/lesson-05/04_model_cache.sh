#!/usr/bin/env bash
cd "$(dirname "$0")"
rm -rf models
mkdir -p models
dd if=/dev/urandom of=models/model_v1.bin bs=1M count=10

echo "-- TODO1 v1 크기:"
docker run --rm -v "$PWD/models":/models:ro python:3.12-slim \
  python -c "import os; print(os.path.getsize('/models/model_v1.bin'))"

echo "-- TODO2 v2(15MB)를 만들고 이미지 재빌드 없이 같은 명령으로:"
dd if=/dev/urandom of=models/model_v2.bin bs=1M count=15
docker run --rm -v "$PWD/models":/models:ro python:3.12-slim \
  python -c "import os; print(os.path.getsize('/models/model_v2.bin'))"
