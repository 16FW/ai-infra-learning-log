# Lesson 08 — 네트워킹과 종합 트러블슈팅

## 핵심 개념

### 장애는 네 층 중 하나에 있다

```
① 프로세스가 떠 있는가?    (ps, systemctl, docker ps)
② 포트를 열고 있는가?      (ss -tlnp)
③ 네트워크로 닿는가?       (DNS, 라우팅, 방화벽, 포트 매핑)
④ 응답이 정상인가?         (curl, HTTP 상태, 앱 로그)
```

**아래 층부터** 확인한다. 프로세스가 죽었는데 방화벽을 뒤지는 건 시간 낭비다.
다만 모든 층을 같은 비중으로 보면 느리므로, **증상에서 가설 순위를 정한다.**
"로컬에선 되는데 외부에서 안 된다"는 증상 자체가 ②의 바인딩 문제를 강하게 시사한다.

### IP, 포트, 바인딩

```
10.0.0.5:8000
  │        └── 포트  → 어떤 프로세스에 전달할지
  └─────────── IP    → 어떤 머신(인터페이스)에 보낼지
```

| 바인딩 주소 | 받는 요청 |
|---|---|
| `127.0.0.1` | loopback 인터페이스로 들어온 요청만 |
| `0.0.0.0` | 머신의 **모든 인터페이스**로 들어온 요청 |

`127.0.0.1`은 "자기 자신에게 들어오는 요청"이 아니라 **loopback 인터페이스로
들어오는 요청**이다. 같은 머신에서 시작한 요청이라도 외부 IP로 접속하면 loopback이
아니라서 받지 못한다. loopback은 `127.0.0.1`만이 아니라 `127.0.0.0/8` 전체다
(`127.0.0.53`, `127.0.0.54`도 로컬 전용).

### 컨테이너에서 이게 장애가 되는 이유

컨테이너는 **자기만의 네트워크 네임스페이스**를 가진다. 컨테이너 안의 `127.0.0.1`은
컨테이너 자신의 loopback이다. 호스트에서 포트 매핑으로 들어오는 요청은 컨테이너의
`eth0`(예: `172.17.0.2`)로 도착한다. 앱이 `127.0.0.1`에만 바인딩돼 있으면 `eth0`로 온
요청은 받지 않는다.

> 핵심은 **요청이 어느 인터페이스로 도착하느냐**다. 그래서 컨테이너 안에서는
> `0.0.0.0`으로 바인딩한다.

### refused와 timeout은 다르다

```
Connection refused → 머신에 닿았고, 그 포트를 듣는 프로세스가 없음.
                     목적지 커널이 적극적으로 거절(RST). 즉시 실패.   → ②를 의심
Timeout            → 패킷이 중간에서 폐기되거나 응답이 없음. 오래 걸림. → ③을 의심
```

K8s에서 "Pod에 접속이 안 된다"를 만났을 때 이 구분이 조사 방향을 바로 갈라준다.
`ping`은 timeout 조사에 쓰지만, ICMP를 막아둔 환경이 많아서 ping 실패가 곧 도달
불가는 아니다.

## 동작 원리

### 포트 → 프로세스를 찾는 원리

```bash
sudo ss -tlnp | grep 8000
```

내부적으로 하는 일은 Lesson 1의 "모든 것은 파일이다" 그대로다:

```
/proc/net/tcp 에서 포트(16진수, 8000 = 1F40) → 소켓 inode
/proc/<PID>/fd/ 안의 "socket:[inode]" 링크와 대조 → PID 특정
```

`ss`의 `Process` 열이 비는 경우가 있다. 내 소유가 아닌 프로세스의 `/proc/<PID>/fd`는
읽을 수 없기 때문이다. (Lesson 2의 권한 개념) `sudo`를 붙이면 보인다.

`ss -tlnp`의 출력에서 읽을 것은 두 가지다. **누가 쓰는가(PID)**, 그리고
**누구에게 열려 있는가(Local Address가 `127.0.0.1`인지 `0.0.0.0`인지)**.

## 실습에서 한 것

### 바인딩 비교

```
LISTEN 0  5   127.0.0.1:8000   0.0.0.0:*   users:(("python3",pid=1227,fd=3))
LISTEN 0  5     0.0.0.0:8000   0.0.0.0:*   users:(("python3",pid=1476,fd=3))
```

달라진 것은 `Local Address` 열 하나다.

### 종합 트러블슈팅 — 서비스가 시작하자마자 죽는다

```python
# app.py
import os
os.chdir("/root/nonexistent")
```

처음 `systemctl status`는 `active (running) ... 18ms ago`였다. `Type=simple`은
프로세스가 뜨자마자 성공으로 판단하기 때문이다. 1초 뒤에 다시 보니:

```
× broken.service
     Active: failed (Result: exit-code)
   Duration: 103ms
    Process: ... (code=exited, status=1/FAILURE)

PermissionError: [Errno 13] Permission denied: '/root/nonexistent'
```

처음엔 `FileNotFoundError`라고 추측했지만 `namei -l`이 반박했다:

```
drwxr-xr-x root root /
drwx------ root root root
                      nonexistent - Permission denied
```

`/root`가 `700`이라 `eunho`는 통과(x)할 수 없다. 통과를 못 하니 `nonexistent`가
있는지 없는지를 **커널이 알려주지 않는다.**

```
open("/root/nonexistent")
   ↓
① /root 통과 가능? (x 비트)  → 아니오 → EACCES (PermissionError)  ← 여기서 끝
   ↓ (통과했다면)
② nonexistent 존재? → 아니오 → ENOENT (FileNotFoundError)
```

**권한 검사가 존재 확인보다 먼저**다. 설계상 의도다. 반대 순서라면 권한 없는
사용자가 "그 파일이 있는지 없는지"를 알아낼 수 있다(정보 누출).

진단 순서:

```
① systemd가 프로그램을 실행했는가?  → status=1 (126/127/203 아님) → 예
② 어디서 죽었는가?                  → journal traceback, app.py line 2
③ 어떤 예외인가?                    → PermissionError
④ 왜?                               → /root가 700, 통과 불가
⑤ 어느 층인가?                      → ① 프로세스 층 (포트 열기 전에 죽음)
```

### 발견: `systemctl start` 성공 ≠ 서비스 정상

`Type=simple` 서비스는 프로세스 생성 즉시 systemd가 성공으로 판단한다. 직후에 예외로
죽어도 `systemctl start` 자체는 성공을 반환한다. 배포 스크립트가 `start` 직후 "배포
완료"를 찍으면 죽어가는 서비스를 정상으로 보고한다.

감지 방법:
- 지연 후 `systemctl is-active` 확인
- 헬스체크를 **재시도하며** 호출 (`curl --retry 5 --retry-connrefused`)
- `Type=notify`: 앱이 준비 완료를 systemd에 직접 알림
- K8s라면 readinessProbe가 이 역할을 한다

### 미해결: 자기 자신에 대한 timeout

`curl -v http://127.0.0.1:9999`가 `Connection refused`가 아니라 135초 후
`Connection timed out`이었다. loopback이 네트워크를 타지 않으므로 이 환경(WSL2)의
이상 신호이며, 원인은 조사하지 않았다.

## Infrastructure 연결

- 컨테이너 `0.0.0.0` 바인딩은 Module 005(Docker)에서 반드시 마주친다.
- "Pod에서 서비스 이름으로 접속이 안 된다" → `/etc/resolv.conf`(Lesson 1)의 DNS 확인.
- 종합 트러블슈팅에 Lesson 1(`namei`), 2(권한), 4(journal), 5(`status=`), Module 001
  (traceback)이 전부 쓰였다. 장애 대응은 개별 지식이 아니라 조합이다.
- `Restart=on-failure`를 걸었다면 이 서비스는 같은 에러로 재시작을 반복했을 것이다.
  원인이 권한이라 재시작해도 고쳐지지 않는다.

## 면접 포인트

- `127.0.0.1`과 `0.0.0.0` 바인딩의 차이, 그리고 컨테이너 장애와의 연결.
- `Connection refused`와 `timed out`의 의미와 조사 방향의 차이.
- "컨테이너화한 API가 외부에서 안 된다" → ① 프로세스 → ② 바인딩 주소 → ③ 포트 매핑·방화벽
  → ④ 응답 순으로, **증상에서 가설 순위를 정한다.**
- `systemctl start`가 성공을 반환했는데 서비스가 죽어 있는 경우의 감지 방법.

## 내 말로 3줄 요약

1. 네트워크 바인딩과 장애 진단: 장애 조치는 프로세스→포트→네트워크→응답 순으로 하위 계층부터 진단하며, 컨테이너 환경에서는 외부/호스트 트래픽 수신을 위해 127.0.0.1이 아닌 0.0.0.0 바인딩이 필수이다.

2. 오류 시그널과 커널 동작: Connection refused(포트 미개설/RST)와 Timeout(네트워크 차단/패킷 유실)을 구분하여 원인을 추론하고, 커널은 보안상 정보 누출을 막기 위해 파일 존재 여부 확인보다 권한 검사를 우선 수행한다.

3. 서비스 상태 검증과 모니터링: systemctl start 실행 성공이 앱의 실질적 정상 작동을 보장하지 않으므로(Type=simple 특성), 헬스체크 재시도(curl --retry), Type=notify, readinessProbe 등으로 실제 상태를 검증해야 한다.
