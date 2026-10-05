# Lesson 03 — 프로세스와 시그널

## 핵심 개념

### 프로세스는 트리다

모든 프로세스는 다른 프로세스가 fork해서 만든다. PID 1만 예외로, 부팅 시
커널이 만든다.

```
PID 1 (init/systemd)
├── sshd
│   └── bash
│       └── python3 train.py
└── docker daemon
    └── containerd-shim
        └── uvicorn
```

- **부모-자식 관계가 생명주기를 지배한다.** 자식이 죽으면 부모가 수거(reap)해야
  완전히 사라진다. 안 하면 좀비(Z)가 남는다.
- **PID 1이 죽으면 그 세계가 끝난다.** 컨테이너에서 `CMD`로 지정한 프로세스가
  PID 1이 되고, 그게 죽는 순간 컨테이너가 종료된다.

### 이름이 아니라 PID로 식별한다

`/init`이라는 이름의 프로세스가 PID 1, 57458, 57459로 세 개 존재할 수 있다.
이름이 같다고 같은 프로세스가 아니다.

```bash
pkill python3     # 학습 job만 죽이려다 서빙 프로세스까지 날아간다
```

### 프로세스 상태

```
R  Running                 실행 중 또는 실행 대기
S  Sleeping                I/O나 이벤트 대기 (대부분의 프로세스)
D  Uninterruptible sleep   디스크 I/O 대기, kill로도 안 죽음
Z  Zombie                  끝났는데 부모가 수거 안 함
T  Stopped                 일시정지
```

`D`가 많으면 디스크 I/O 병목, `Z`가 쌓이면 부모 프로세스 버그.

### VSZ vs RSS

- **VSZ** (Virtual Size): 예약한 가상 메모리. 실제로 안 쓰는 것도 포함
- **RSS** (Resident Set Size): **실제 물리 메모리에 올라간 양**

docker 프로세스: VSZ 1.2GB vs RSS 26MB — 50배 차이.
메모리 문제는 **RSS를 봐야 한다.** PyTorch는 CUDA 초기화 때 거대한 가상 주소
공간을 잡아서 VSZ가 수십 GB로 찍히지만 실제 사용량이 아니다.

## 동작 원리

### kill은 종료 명령이 아니라 시그널 전송이다

```
kill -TERM  → 애플리케이션에 전달 → 애플리케이션이 판단
kill -KILL  → 커널이 즉시 제거     → 애플리케이션은 알지도 못함
```

`TERM`은 TERMINATE의 약자이자 **종료 요청**이다. 명령이 아니다. 받는 쪽은
요청대로 정리하고 종료할 수도, 무시할 수도, 다른 일을 할 수도 있다
(`SIGHUP`을 받으면 설정 파일을 다시 읽는 서버가 많다).

**SIGKILL과 SIGSTOP은 프로세스가 가로챌 수 없는 유일한 두 시그널**이다.
핸들러 등록 자체가 불가능하다.

| 시그널 | 번호 | 발생 | 가로채기 | 기본 동작 |
|---|---|---|---|---|
| SIGINT | 2 | Ctrl+C | 가능 | 종료 |
| SIGTERM | 15 | `kill` 기본값 | 가능 | 종료 |
| SIGKILL | 9 | `kill -9` | **불가** | 즉시 제거 |
| SIGHUP | 1 | 터미널 끊김 | 가능 | 종료 (설정 재읽기로도 씀) |

> 순서는 항상 `-TERM` 먼저, 안 되면 `-9`.
> `-9`를 습관적으로 쓰면 쓰다 만 파일, 좀비 커넥션, 안 지워진 락 파일이 남는다.

### Python의 시그널 처리

Python은 SIGINT에만 기본 핸들러를 걸어 **예외(`KeyboardInterrupt`)로 변환**해준다.
SIGTERM은 기본 동작이 즉시 종료라 직접 등록해야 잡힌다.

→ "Ctrl+C는 잡히는데 `kill`은 안 잡힌다"의 원인.
→ 로컬에서 Ctrl+C로만 테스트하면 프로덕션(SIGTERM)에서 매번 강제 종료된다.

### Ctrl+C는 프로세스 그룹에 보낸다

```bash
python3 script.py | tee output.log
```

Ctrl+C는 `python3`와 `tee` **둘 다** 받는다. `kill -INT <PID>`는 그 PID 하나에만
간다. (포그라운드 프로세스 그룹)

## 실습에서 한 것

시그널 핸들러를 등록한 스크립트로 세 경로를 전부 검증했다.

```
kill -TERM  → [신호 15 수신] 정리 작업 중... → [정리 완료] 종료합니다
Ctrl+C      → [신호 2 수신]  정리 작업 중... → [정리 완료] 종료합니다
kill -KILL  → Killed                          (정리 기회 없음)
```

핸들러를 등록하지 않으면 SIGINT는 `KeyboardInterrupt` 스택트레이스로 나온다.

`ps` 활용:

```bash
ps aux --sort=-%cpu | head -6     # CPU 상위 (- 는 내림차순)
ps aux --sort=-%mem | head -4     # 메모리 상위
ps -ef --forest                   # 트리 구조
```

CPU/메모리 급증 알림을 받았을 때 제일 먼저 치는 명령.

추가로 확인한 것: `ps -ef --forest`에서 `-bash`처럼 이름 앞에 `-`가 붙으면
**로그인 셸**이다. 로그인 셸은 `.bash_profile`, 비로그인 셸은 `.bashrc`를 읽는다.
"직접 실행하면 되는데 cron으로 돌리면 command not found"의 원인.

## Infrastructure 연결

### Graceful Shutdown

K8s가 Pod를 종료할 때:

```
1. SIGTERM 전송
2. terminationGracePeriodSeconds(기본 30초) 대기
3. 그래도 안 죽으면 SIGKILL
```

30초를 기다리는 이유는 **처리 중인 요청을 끝낼 시간**을 주기 위해서다.
SIGKILL을 받으면 클라이언트는 응답 대신 연결 끊김(connection reset)을 받는다.

애플리케이션이 SIGTERM을 받았을 때 해야 할 일:

```python
def handler(sig, frame):
    # ① 새 트래픽 차단 — health 엔드포인트를 실패로 전환
    app.state.shutting_down = True
    time.sleep(5)              # K8s가 엔드포인트에서 빼갈 시간

    # ② 처리 중인 요청 완료 대기 (drain)
    server.shutdown()
    wait_for_active_requests()

    # ③ 자원 정리
    db_pool.close()
    torch.cuda.empty_cache()
    log_handler.flush()

    sys.exit(0)
```

**순서가 중요하다.** ②를 ① 전에 하면 새 트래픽이 계속 들어와서 in-flight 요청이
영원히 0이 되지 않는다.

①에서 쓰는 health 엔드포인트가 Module 001에서 exit code로 만든 health check의
HTTP 버전이다.

### SIGTERM을 무시하면

```
배포 시작 → SIGTERM → 앱이 무시 → 30초 대기 → SIGKILL
```

**모든 배포가 30초씩 지연되고 매번 SIGKILL로 끝난다.** Pod가 10개면 롤링
업데이트에 5분이 추가되고, 매 Pod마다 처리 중이던 요청이 끊겨 에러율 그래프에
스파이크가 찍힌다.

### Docker CMD 형식 함정

```dockerfile
CMD python app.py              # ❌ sh가 PID 1, 시그널을 자식에 전달 안 함
CMD ["python", "app.py"]       # ✅ python이 PID 1
```

핸들러를 다 짜놓고도 "왜 안 되지?"로 헤매는 원인.

## 면접 포인트

- `kill`은 종료 명령이 아니라 시그널 전송이다. SIGKILL만 가로챌 수 없다.
- Graceful Shutdown 3단계를 **순서까지** 설명할 수 있어야 한다.
  (트래픽 차단 → drain → 자원 정리)
- 메모리 문제를 볼 때 VSZ가 아니라 RSS를 본다.

## 내 말로 3줄 요약

1. 프로세스는 트리 구조와 PID로 관리된다: 모든 프로세스는 부모-자식 관계를 가지며,
   이름이 같아도 고유한 PID로 식별하고 메모리는 실사용량인 RSS를 기준으로 본다.
2. `kill`은 종료 명령이 아닌 시그널 전송이다: `SIGTERM`(15)은 앱이 정리할 시간을 주는
   요청이고, `SIGKILL`(9)만 가로챌 수 없는 강제 종료다.
3. Graceful Shutdown은 무중단 배포의 핵심이다: 안전한 종료를 위해선 SIGTERM 수신 시
   ① 새 트래픽 차단 ② 진행 중 요청 완료(drain) ③ 자원 정리 순서를 엄격히 지켜야 한다.
