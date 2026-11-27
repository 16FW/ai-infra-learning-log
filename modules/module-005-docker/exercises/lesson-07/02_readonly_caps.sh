docker run -d --name ro1 --read-only -p 8001:8000 lesson07:hard
sleep 3
curl -s localhost:8001/health                      # TODO 1: 기동하는지 기록
docker exec ro1 touch /tmp/a                       # TODO 2: 결과 기록
docker rm -f ro1

docker run -d --name ro2 --read-only --tmpfs /tmp \
  --cap-drop ALL --security-opt no-new-privileges -p 8001:8000 lesson07:hard
sleep 3
curl -s localhost:8001/health                      # TODO 3: 기동하는지 기록
docker exec ro2 touch /tmp/a                       # TODO 4: 이번엔 결과가?
docker exec ro2 touch /app/app/x                   # TODO 5: 결과 기록
docker rm -f ro2
