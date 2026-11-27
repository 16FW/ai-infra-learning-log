#!/usr/bin/env bash
docker rm -f apiA apiB >/dev/null 2>&1
docker network rm mynet >/dev/null 2>&1

echo "== 1) 기본 bridge =="
docker run -d --name apiA lesson04:app >/dev/null
sleep 3
echo "-- TODO4 이름으로:"
docker run --rm curlimages/curl curl -sS -m 3 http://apiA:8000/health; echo "  (exit=$?)"
IP=$(docker inspect -f '{{.NetworkSettings.IPAddress}}' apiA)
echo "-- TODO4b IP($IP)로:"
docker run --rm curlimages/curl curl -sS -m 3 http://$IP:8000/health; echo "  (exit=$?)"

echo "== 2) 사용자 정의 bridge =="
docker network create mynet >/dev/null
docker run -d --name apiB --network mynet lesson04:app >/dev/null
sleep 3
echo "-- TODO5 이름으로:"
docker run --rm --network mynet curlimages/curl curl -sS -m 3 http://apiB:8000/health; echo "  (exit=$?)"
echo "-- TODO6 네트워크 안의 컨테이너 IP:"
docker network inspect mynet -f '{{range .Containers}}{{.Name}} {{.IPv4Address}}{{"\n"}}{{end}}'
docker network inspect mynet -f 'subnet: {{range .IPAM.Config}}{{.Subnet}}{{end}}'

docker rm -f apiA apiB >/dev/null
docker network rm mynet >/dev/null
