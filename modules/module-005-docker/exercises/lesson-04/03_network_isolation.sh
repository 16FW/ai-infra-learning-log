#!/usr/bin/env bash
docker rm -f a1 b1 >/dev/null 2>&1
docker network rm netA netB >/dev/null 2>&1
docker network create netA >/dev/null
docker network create netB >/dev/null
docker run -d --name a1 --network netA lesson04:app >/dev/null
docker run -d --name b1 --network netB lesson04:app >/dev/null
sleep 3

echo "-- TODO1 netA -> a1 (같은 네트워크):"
docker run --rm --network netA curlimages/curl curl -sS -m 5 http://a1:8000/health; echo "  (exit=$?)"
echo "-- TODO2 netA -> b1 (다른 네트워크):"
docker run --rm --network netA curlimages/curl curl -sS -m 5 http://b1:8000/health; echo "  (exit=$?)"

echo "-- TODO3 b1을 netA에도 연결한 뒤:"
docker network connect netA b1
docker network inspect netA -f '{{range .Containers}}{{.Name}} {{.IPv4Address}}{{"\n"}}{{end}}'
docker run --rm --network netA curlimages/curl curl -sS -m 5 http://b1:8000/health; echo "  (exit=$?)"

echo "-- TODO4 외부 접속(기본 bridge):"
docker run --rm curlimages/curl curl -sS -m 5 -o /dev/null -w "%{http_code}\n" https://example.com; echo "  (exit=$?)"

docker rm -f a1 b1 >/dev/null
docker network rm netA netB >/dev/null
