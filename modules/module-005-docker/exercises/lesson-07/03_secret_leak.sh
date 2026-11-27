docker build -f Dockerfile.secret --build-arg API_KEY=FAKE-key-67890 -t lesson07:secret .

# (a)
docker inspect lesson07:secret --format '{{.Config.Env}}'
# TODO 1: DB_PASSWORD 가 보이는지 기록

# (b)
docker history --no-trunc lesson07:secret | grep -i "api_key"
# TODO 2: API_KEY 값이 보이는지 기록 (안 보이면 그것도 기록)

# (c) 이미지를 풀어서 .env 가 레이어에 남아 있는지 확인
docker save lesson07:secret -o /tmp/s.tar
mkdir -p /tmp/s && tar -xf /tmp/s.tar -C /tmp/s
for f in /tmp/s/blobs/sha256/*; do tar -tf "$f" 2>/dev/null | grep -q "app/.env" && echo "발견: $f"; done
# TODO 3: .env 가 들어 있는 레이어가 있는지 기록
#   발견되면: tar -xOf <그 파일> app/.env   (내용이 보이는지)
rm -rf /tmp/s /tmp/s.tar            # 반드시 정리 (디스크)

# (d)
docker run -d --name e1 -e RUNTIME_SECRET=FAKE-run-1 lesson07:secret
docker inspect e1 --format '{{.Config.Env}}' | tr ' ' '\n' | grep RUNTIME
docker inspect lesson07:secret --format '{{.Config.Env}}' | grep -c RUNTIME
# TODO 4: 컨테이너에는 보이고 이미지에는 안 보이는지 기록
docker rm -f e1
