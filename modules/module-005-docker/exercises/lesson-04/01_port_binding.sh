#!/usr/bin/env bash
cd "$(dirname "$0")"
docker rm -f api1 api2 >/dev/null 2>&1

echo "== 1) --host 127.0.0.1 =="
docker run -d --name api1 -p 8000:8000 lesson04:app \
  uvicorn app.main:app --host 127.0.0.1 --port 8000 >/dev/null
sleep 3
docker port api1
docker logs api1 2>&1 | grep -i "running on"
echo "-- TODO1 호스트에서:"
curl -sS -m 3 localhost:8000/health; echo "  (curl exit=$?)"
echo "-- TODO2 컨테이너 안에서:"
docker exec api1 python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/health').read())"
docker rm -f api1 >/dev/null

echo "== 2) --host 0.0.0.0 =="
docker run -d --name api2 -p 8000:8000 lesson04:app \
  uvicorn app.main:app --host 0.0.0.0 --port 8000 >/dev/null
sleep 3
docker port api2
docker logs api2 2>&1 | grep -i "running on"
echo "-- TODO3 호스트에서:"
curl -sS -m 3 localhost:8000/health; echo "  (curl exit=$?)"
docker rm -f api2 >/dev/null
