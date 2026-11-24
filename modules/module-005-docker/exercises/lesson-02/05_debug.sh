#!/usr/bin/env bash
docker rm -f broken dbg >/dev/null 2>&1
docker run -d --name broken python:3.12-slim \
  python -c "print('boot'); open('/data/x','w')" >/dev/null
sleep 2
docker ps -a --filter name=broken                              # 상태: Exited (1)
docker logs broken                                             # 트레이스백: /data 없음
docker inspect -f 'exit={{.State.ExitCode}} cmd={{.Config.Cmd}}' broken
docker cp broken:/etc/os-release ./os-release.txt && head -2 os-release.txt   # 죽은 컨테이너에서도 복사됨
docker exec broken ls / 2>&1 | head -1                         # 실패: 실행 중이 아님
docker commit broken dbg >/dev/null                            # 죽은 상태를 이미지로 저장
docker run --rm --entrypoint sh dbg -c 'ls /; ls /data 2>&1'   # 같은 파일시스템에서 원인 확인
docker rm -f broken; docker rmi dbg; rm -f os-release.txt
