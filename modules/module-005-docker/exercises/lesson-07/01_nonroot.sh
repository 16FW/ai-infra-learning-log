docker build -f Dockerfile.root -t lesson07:root .
docker build -f Dockerfile.hardened -t lesson07:hard .

docker run -d --name r1 lesson07:root
docker run -d --name h1 lesson07:hard
docker exec r1 id             # TODO 1: 결과 기록
docker exec h1 id             # TODO 2: 결과 기록
docker exec h1 touch /app/x   # TODO 3: 결과 기록 (root 소유 폴더에 쓰기)
docker exec h1 touch /app/app/x   # TODO 4: 결과 기록 (--chown 된 폴더에 쓰기)
docker ps                     # TODO 5: h1 의 STATUS 에 (healthy) 가 보이는지
docker rm -f r1 h1
