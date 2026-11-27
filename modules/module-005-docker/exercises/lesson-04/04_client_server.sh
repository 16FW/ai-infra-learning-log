#!/usr/bin/env bash
docker rm -f api holder >/dev/null 2>&1
docker network rm appnet >/dev/null 2>&1
docker network create appnet >/dev/null
show() { docker network inspect appnet -f '{{range .Containers}}{{.Name}} {{.IPv4Address}}{{"\n"}}{{end}}'; }

echo "== TODO1 api 실행 (-p 없음) =="
docker run -d --name api --network appnet lesson04:app >/dev/null
sleep 3

echo "-- TODO2 client -> api (이름, POST):"
docker run --rm --network appnet curlimages/curl curl -sS -m 5 -X POST "http://api:8000/predict?x=3"; echo "  (exit=$?)"

echo "-- TODO3 호스트에서:"
curl -sS -m 3 localhost:8000/health; echo "  (exit=$?)"

echo "== TODO4 api 삭제 후 같은 이름으로 재생성 =="
echo "-- 변경 전:"; show
docker rm -f api >/dev/null
docker run -d --name holder --network appnet alpine sleep 120 >/dev/null   # 옛 IP를 다른 컨테이너가 차지
docker run -d --name api --network appnet lesson04:app >/dev/null
sleep 3
echo "-- 변경 후:"; show
echo "-- client 호출:"
docker run --rm --network appnet curlimages/curl curl -sS -m 5 -X POST "http://api:8000/predict?x=3"; echo "  (exit=$?)"

docker rm -f api holder >/dev/null
docker network rm appnet >/dev/null
