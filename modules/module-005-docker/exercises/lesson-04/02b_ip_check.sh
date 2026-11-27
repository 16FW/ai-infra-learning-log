#!/usr/bin/env bash
docker rm -f apiA >/dev/null 2>&1
docker run -d --name apiA lesson04:app >/dev/null
sleep 3
IP=$(docker inspect -f '{{.NetworkSettings.Networks.bridge.IPAddress}}' apiA)
echo "apiA IP: $IP"
echo "-- TODO4b IP로:"
docker run --rm curlimages/curl curl -sS -m 3 http://$IP:8000/health; echo "  (exit=$?)"
echo "-- 기본 bridge 서브넷:"
docker network inspect bridge -f '{{range .IPAM.Config}}{{.Subnet}}{{end}}'
echo "-- 기본 bridge의 resolv.conf:"
docker run --rm alpine cat /etc/resolv.conf
docker network create mynet >/dev/null
echo "-- 사용자 정의 bridge의 resolv.conf:"
docker run --rm --network mynet alpine cat /etc/resolv.conf
docker network rm mynet >/dev/null
docker rm -f apiA >/dev/null
