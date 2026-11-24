# Lesson 2. 도커 컨테이너 활용

## 핵심 개념
- 수명주기: created → running → exited(code) → removed. `stop`은 SIGTERM 후 유예 시간 뒤 SIGKILL, `kill`은 즉시 SIGKILL, `rm -f`는 SIGKILL 후 삭제.
- PID 1은 핸들러를 등록하지 않은 시그널을 커널이 무시한다. 앱이 PID 1이면 SIGTERM을 받아도 죽지 않는다. 해결은 SIGTERM 핸들러, exec form `CMD`, `--init`(tini: 신호 전달 + 좀비 회수).
- `--restart` 정책은 재시작 간격을 지수 백오프(100ms에서 시작해 두 배씩)로 늘린다.
- `--cpus`는 `cpu.max`(quota/period)로 사용 시간에 상한을 건다. CPU는 압축 가능한 자원이라 throttling으로 느려질 뿐 죽지 않는다. 메모리는 압축 불가라 한도를 넘으면 OOM kill이 된다.
- 죽은 컨테이너 디버깅 순서: `logs`(왜) → `inspect`(어떻게) → `exec`(실행 중일 때만) → `cp` → `commit` + `--entrypoint sh`.

## 동작 원리
- exit 137 = SIGKILL(128+9), 143 = SIGTERM(128+15). `--init`을 쓰면 tini가 SIGTERM을 자식에게 전달하고, 자식이 시그널로 죽으면 143으로 끝난다.
- `cpu.max`가 `50000 100000`이면 100ms 주기마다 50ms만 CPU를 쓸 수 있다. 초과하면 커널이 프로세스를 멈춘다(`nr_throttled` 증가).
- `docker stats`의 MEM LIMIT은 cgroup 값이고, 컨테이너 안의 `free`는 호스트 값이다.
- 파이프로 연결된 stdout만 버퍼링되어 로그 순서가 뒤바뀔 수 있다. Python 서비스는 `PYTHONUNBUFFERED=1`이 필요하다.

## 실습에서 한 것
- 측정 조건: nproc=4, load average 1.05/1.66/1.70.
- 종료 처리: 핸들러 없음 1.2초·137, 핸들러 있음 0.3초·exit 0, 핸들러 없음 + `--init` 0.2초·143. `StopTimeout=1`이라 기본 10초가 아니라 약 1초에 SIGKILL이 갔다(이 값의 출처는 미확인).
- 재시작: `on-failure:3`에서 `RestartCount=3`, 최종 exited(1), 간격 0.325 → 0.388 → 0.583초.
- CPU 제한: `cpu.max=50000 100000`, stats 50.18%, `nr_throttled=66`, 제한 없을 때 93.48%. 죽지 않았다.
- 디버깅: 죽은 컨테이너도 `docker cp`가 되고(심볼릭 링크는 `-L`), `commit` + `--entrypoint sh`로 같은 파일시스템을 열어 원인(`/data` 없음)을 확인했다.

## Infrastructure 연결
- `docker stop` → Pod 종료의 `terminationGracePeriodSeconds`, `--restart` → `restartPolicy` + `CrashLoopBackOff`, `--cpus`/`--memory` → CPU/메모리 limit.
- ML 서빙에서는 torch 스레드 수가 호스트 코어 기준이라 CPU limit보다 많으면 평균 CPU%가 낮아도 p99 지연이 커진다.
- graceful shutdown은 readiness 실패 → 짧은 대기 → 진행 중 요청 마무리 → 종료 순서로, 유예 시간이 이 전체보다 길어야 한다.

## 면접 포인트
- `docker stop`이 느리거나 137로 끝나면 PID 1이 SIGTERM을 처리하지 못하는 경우를 먼저 의심한다(shell form `CMD`, 핸들러 없음).

## 내 말로 3줄 요약
1. `docker stop`은 SIGTERM 후 유예, 그래도 안 죽으면 SIGKILL인데, PID 1은 핸들러 없는 SIGTERM을 무시하므로 핸들러·exec form·`--init`으로 graceful shutdown을 보장해야 한다.
2. CPU는 쓰는 시간을 깎는(throttling) 압축 가능 자원이라 느려지기만 하고, 메모리는 압축 불가라 초과하면 OOM kill이 된다. 둘 다 컨테이너 안의 `nproc`/`free`가 아니라 cgroup 파일로 확인한다.
3. 죽은 컨테이너는 `logs`(왜) → `inspect`(어떻게) 순으로 좁히고, restart 정책은 증상을 가리지 않게 백오프와 재시작 횟수 확인을 함께 본다.
