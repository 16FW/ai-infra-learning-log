# Lesson 1. 컨테이너 소개

## 핵심 개념
- 컨테이너 = 호스트 커널을 공유하는 일반 프로세스 + namespace(보이는 범위 격리) + cgroup(쓸 수 있는 자원 제한)
- 이미지 = 읽기 전용 레이어 스택, 컨테이너 = 이미지 + 쓰기 가능한 레이어 + 실행 중인 프로세스
- VM은 게스트 커널을 따로 부팅하고, 컨테이너는 커널을 공유한다. 가볍고 빠르지만 호스트 커널에 종속된다.

## 동작 원리
- PID namespace: 같은 프로세스가 컨테이너 안에서는 PID 1, 호스트에서는 다른 번호(예: 77211)로 보인다.
- UTS namespace: hostname이 분리된다. `unshare --pid --fork --mount-proc --uts`로 직접 재현했다.
- cgroup v2: `--memory=100m`은 `memory.max=104857600`이 된다. 초과하면 커널이 회수를 시도하고, 그래도 부족하면 OOM killer가 SIGKILL을 보낸다(exit 137, `OOMKilled=true`).
- `free`, `/proc/meminfo`는 cgroup 제한을 반영하지 않는다. 컨테이너 안의 실제 한도는 `/sys/fs/cgroup/memory.max`에서 읽는다.
- 레이어: `RUN`/`COPY`마다 레이어가 생긴다. `rm`은 파일을 지우지 못하고 삭제 표시(whiteout)만 얹는다. 빌드 캐시는 위에서부터 이어지다가 처음 바뀐 단계부터 아래가 모두 무효가 된다.

## 실습에서 한 것
- namespace: `unshare`로 만든 bash에서 PID 1, `ps`에는 bash와 ps만 보였고, hostname을 바꿔도 호스트는 그대로였다.
- memhog (`--memory=100m`): swap이 허용되어(`memory.swap.max`=100MiB) allocated 190MB까지 갔다. 이때 RSS는 104MB였다.
- memhog (`--memory=100m --memory-swap=100m`): allocated 90MB에서 OOMKilled(137)가 났다.
- RSS 104MB = RssAnon 99 + RssFile 5. 한도에 청구된 `memory.current`는 약 99.5MiB였다.
- 레이어: 분리된 RUN은 dd 레이어 52.4MB와 rm 레이어 4.1kB가 남아 50MB가 이미지에 그대로 있었다. 합친 RUN(`dd && rm`)은 50MB 레이어가 없었다(레이어 7개 vs 6개).
- 캐시: `memhog.py`만 바꾸면 `COPY` 레이어만 재실행됐다. `COPY`를 맨 위로 옮기면 아래 단계가 전부 재실행됐다.
- Docker Desktop(WSL2)에서는 컨테이너 프로세스가 내 Ubuntu의 `ps`에 보이지 않았다. 데몬이 별도 distro에서 돌기 때문으로 추정한다(미검증).
- `docker image inspect .Size`는 압축 크기라서, 0으로 채운 50MB 파일이 있어도 세 이미지가 같게 나왔다. 레이어 크기는 `docker history`로 본다.

## Infrastructure 연결
- 로컬에서 되던 모델 서버가 Pod에서 OOMKilled가 되는 이유: Kubernetes는 swap 없이 운영하는 경우가 많아서 `--memory-swap` 실험 쪽에 가깝다. limit은 워밍업 후 RSS가 아니라 cgroup 청구량(`working_set`) 기준으로 잡는다.
- `os.cpu_count()`, `psutil.virtual_memory()`는 호스트 값을 본다. worker/스레드 수를 자동으로 정하면 limit을 넘길 수 있다.
- 레이어 순서가 곧 배포 속도다. 의존성 → 모델 가중치 → 코드 순으로 쌓는다.
- 비밀 키를 `COPY`한 뒤 `rm`해도 레이어에 남는다(Lesson 7).

## 면접 포인트
- 컨테이너는 VM이 아니라 namespace와 cgroup으로 격리된 호스트 커널 위의 프로세스이고, exit code 137은 OOM 전용이 아니라 SIGKILL(128+9) 일반이다.

## 내 말로 3줄 요약
1. 컨테이너는 가상 머신이 아니라, namespace로 시야를 가르고 cgroup으로 자원을 제한한 호스트 커널 위의 프로세스다.
2. 이미지는 불변 레이어의 스택이라 `rm`은 크기를 줄이지 못하고, 캐시는 위에서부터 깨지므로 자주 바뀌는 것을 아래에 둬야 한다.
3. 컨테이너 안의 `free`는 거짓말을 하니 한도는 `memory.max`로 확인하고, 137을 보면 OOM만 의심하지 말고 SIGKILL의 출처를 추적한다.
