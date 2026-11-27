#!/usr/bin/env bash
docker compose up -d --build
docker compose ps
docker network ls
for i in 1 2 3; do
  curl -s -w '  [HTTP %{http_code}]\n' localhost:8000/hits
done
docker compose logs api | tail -5
docker compose exec api python -c "import socket; print(socket.gethostbyname('redis'))"
