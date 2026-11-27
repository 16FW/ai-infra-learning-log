#!/usr/bin/env bash
time docker compose -f compose.health.yaml up -d --build --wait
docker compose -f compose.health.yaml ps
curl -s -w "\n[HTTP %{http_code}]\n" localhost:8000/hits

docker compose -f compose.health.yaml stop redis
sleep 15
docker compose -f compose.health.yaml ps
curl -s -w "\n[HTTP %{http_code}]\n" localhost:8000/health
curl -s -w "\n[HTTP %{http_code}]\n" localhost:8000/hits

docker compose -f compose.health.yaml down -v
