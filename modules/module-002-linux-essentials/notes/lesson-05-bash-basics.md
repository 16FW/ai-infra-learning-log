# Lesson 05 — Bash 스크립팅 기초

## 핵심 개념

### 왜 Python이 있는데 Bash인가

Bash는 **명령어들을 엮는** 데 특화되어 있고, Python은 **로직을 짜는** 데
특화되어 있다.

```bash
docker build -t app . && docker push app && kubectl rollout restart deploy/app
```

같은 일을 Python으로 하려면 subprocess, 에러 처리, 반환값 검사가 필요하다.

그리고 인프라에서는 피할 수 없다:
- Dockerfile의 `RUN`은 전부 shell 명령
- 컨테이너 entrypoint는 거의 항상 `.sh`
- CI/CD 파이프라인의 각 step (GitHub Actions의 `run:`)
- K8s의 `command:`, `lifecycle.preStop`

**경계선**: 100줄을 넘거나 복잡한 자료구조·에러 처리가 필요하면 Python으로
넘어가는 게 맞다. Bash로 JSON을 파싱하고 있다면 이미 잘못된 길.

### Bash는 접착제다

> Bash는 "명령어를 실행하고, 그 종료 코드와 출력을 엮는" 접착제(glue)다.

**① 모든 것은 문자열이다**

```bash
x=5
y=$x+1        # y는 6이 아니라 문자열 "5+1"
```

숫자 타입이 없다. 산술은 `$(( ))`를 써야 한다.

**② 제어 흐름은 종료 코드로 돈다**

```bash
if grep "error" app.log; then
    echo "에러 발견"
fi
```

`if`가 검사하는 건 `grep`의 **exit code**다. 0이면 참, 0이 아니면 거짓.
Python의 `if x > 5:`와 근본이 다르다 — Bash의 `if`는 **명령을 실행하고 성공
여부를 본다.** `[ ]`도 문법이 아니라 `test`라는 **명령어**다.

### x 비트와 shebang

둘은 역할이 다르다.

| | `x` 비트 | shebang |
|---|---|---|
| 없으면 | 실행 자체 거부 (`Permission denied`) | 셸 호출 시엔 호출 셸이 처리, 셸을 안 거치면 실패 |
| 누가 보는가 | 커널의 권한 검사 | 커널의 프로그램 로더 |

shebang이 없어도 **셸에서 `./script.sh`로 호출하면** 동작한다. POSIX 규약상
호출한 셸이 셸 스크립트로 간주해 처리하기 때문이다. 하지만:

- **systemd** (`ExecStart=`), **Docker** (`CMD ["..."]`), **K8s** (`command:`)는
  셸을 거치지 않고 커널에게 직접 실행을 요청한다 → shebang 없으면
  `Exec format error` (`status=203/EXEC`)

`/bin/sh`는 Ubuntu에서 `dash`를 가리키는 심볼릭 링크다. bash 전용 문법
(`[[ ]]`, 배열)을 `sh`로 실행하면 깨진다 — "로컬에선 되는데 CI에선 안 된다"의
흔한 원인.

### 변수는 항상 큰따옴표로 감싼다

Bash는 변수를 치환한 **다음에 단어 분리(word splitting)**를 한다.

```
FILE="my report.txt"

ls -l $FILE
  ① 치환:  ls -l my report.txt
  ② 분리:  ls -l "my" "report.txt"     ← 인자 2개

ls -l "$FILE"
  → 인자 1개
```

따옴표는 ②를 막는다. 실제 사고:

```bash
BACKUP_DIR="/data/old backups"
rm -rf $BACKUP_DIR        # rm -rf /data/old 와 rm -rf backups
```

예외를 따지기보다 **항상 감싸는 습관**이 낫다.

### ./ 와 . (source)는 다르다

| | `./script.sh` | `. script.sh` (source) |
|---|---|---|
| 실행 주체 | 새 자식 프로세스 | **현재 셸 자신** |
| shebang | 읽힘 | 무시됨 |
| `x` 비트 | 필요 | 불필요 |
| `exit` | 자식만 종료 | **현재 셸이 종료됨** |
| 변수 | 자식에만 적용 | 현재 셸에 남음 |

`source`는 `.bashrc`나 `source venv/bin/activate`처럼 **현재 셸의 환경을
바꾸려는 목적**일 때만 쓴다.

### PATH와 ./

명령어를 칠 때 셸은 `PATH`에 등록된 디렉토리만 뒤진다. 현재 디렉토리(`.`)는
보안상 일부러 제외돼 있다 — 누가 `/tmp`에 `ls`라는 악성 스크립트를 두면 거기서
`ls`를 친 사람이 그걸 실행하게 되니까.

그래서 현재 디렉토리의 스크립트는 `./`로 명시해야 한다.

## 동작 원리

### 기계용 출력을 파싱한다

```bash
df -P "$TARGET_DIR" | tail -1 | awk '{print $5}' | tr -d '%'
```

`df -h`는 사람용이라 파일시스템 이름이 길면 **줄을 바꿔서** 출력한다.
그러면 `awk '{print $5}'`가 엉뚱한 값을 집는다. `df -P`(POSIX 형식)는
줄바꿈하지 않도록 보장한다.

> 스크립트가 명령어 출력을 파싱할 때는 사람용 형식이 아니라 기계용 형식을 쓴다.

같은 이유로 `kubectl get pod -o json`, `docker ps --format` 옵션이 존재한다.

### stdout과 stderr 분리

```bash
echo "Error: ..." >&2      # 에러는 stderr로
```

분리해두면 이런 게 가능해진다:

```bash
./disk-check.sh /data 2>/dev/null     # 에러만 숨기기
./disk-check.sh /data > report.txt    # 정상 출력만 파일로, 에러는 화면에
```

### 설정을 코드에서 분리

```bash
THRESHOLD="${THRESHOLD:-80}"     # 환경변수가 없으면 기본값
```

서버마다 임계값이 다를 수 있고, 테스트할 때 `THRESHOLD=0 ./script.sh`로
경고 경로를 즉시 검증할 수 있다. Lesson 1의 `/etc`(설정) vs `/usr`(프로그램)
분리가 스크립트 레벨에서 재현된 것.

## 실습에서 한 것

`disk-check.sh` 작성 — 경로를 받아 디스크 사용률을 검사하고 exit code로 보고.

구조:

```
① 설정        THRESHOLD, TARGET_DIR (기본값 포함)
② 입력 검증   -e 로 경로 존재 확인 → 없으면 exit 2
③ 데이터 수집 df 파이프 파싱
④ 결과 검증   빈 값이면 exit 3
⑤ 판단        임계값 이상이면 exit 1, 아니면 exit 0
```

Module 001 Lesson 2의 "Fail Fast, Handle at the Boundary"와 같은 구조다.
각 단계에서 조건이 안 맞으면 즉시 고유한 exit code로 빠지고, 통과한 것만
다음 단계로 간다.

검증 도구:

```bash
bash -n script.sh          # 문법만 검사 (실행 안 함). CI 린팅에 사용
THRESHOLD=0 ./script.sh /  # 경고 경로를 실제로 실행
```

### systemd 연결로 exit code 확인

```ini
[Service]
Type=oneshot
User=eunho
Environment=THRESHOLD=80
ExecStart=/home/eunho/scripts/disk-check.sh /
```

```
THRESHOLD=80 → ○ inactive (dead)              exit 0
THRESHOLD=0  → × failed (Result: exit-code)   status=1/FAILURE
```

exit code 하나로 systemd의 판단이 완전히 갈린다.

## Infrastructure 연결

```
Bash 스크립트가 exit 1
      ↓
systemd가 "실패"로 해석  →  × failed (Result: exit-code)
      ↓ 같은 원리
Kubernetes가 "Pod 비정상"으로 해석  →  Pod 재시작
```

> exit code는 프로세스가 외부 세계와 소통하는 유일한 표준 신호다.
> systemd도, K8s도, CI 파이프라인도 전부 이것만 본다.

`status=` 값으로 원인을 좁힌다:

| 표시 | 의미 |
|---|---|
| `status=1/FAILURE` | 프로그램이 스스로 1을 반환 (로직 실패) |
| `status=126` | 실행 권한 없음 (**x 비트**) |
| `status=127` | 명령을 못 찾음 (경로/PATH) |
| `status=203/EXEC` | shebang 오류, 실행 형식 불일치 |
| `signal=SIGKILL` | 커널이 죽임 (OOM 등) |

### livenessProbe에 아무거나 쓰면 안 된다

`disk-check.sh`를 livenessProbe로 쓰면:

디스크 85% → exit 1 → Pod 재시작 → **디스크는 그대로** → 또 exit 1 →
**CrashLoopBackOff**

애플리케이션은 멀쩡히 동작하고 있었는데 probe가 죽인 것이다.
모니터링이 장애를 감지한 게 아니라 **모니터링이 장애를 만들었다.**

> livenessProbe는 "재시작하면 고쳐지는 문제"만 검사해야 한다.

| 증상 | 재시작으로 해결? | 적절한 대응 |
|---|---|---|
| 프로세스 데드락 | ✓ | livenessProbe |
| 메모리 누수로 응답 불가 | ✓ | livenessProbe |
| 디스크 가득 참 | ✗ | **알림(Alert)** |
| DB 연결 끊김 | ✗ | readinessProbe (트래픽만 차단) |
| 외부 API 장애 | ✗ | 알림 + 서킷 브레이커 |

probe는 *자동 조치*를, 알림은 *사람의 판단*을 유발한다. 디스크 문제는 로그를
지우든 볼륨을 늘리든 판단이 필요하므로 자동 조치 대상이 아니다.

## 면접 포인트

- `rm -rf $DIR`과 `rm -rf "$DIR"`의 차이와 위험성.
- 스크립트에서 `df -h` 대신 `df -P`를 쓰는 이유.
- `status=126`의 원인과 해결 (x 비트, 상위 디렉토리 x).
- **디스크 체크를 livenessProbe로 쓰면 안 되는 이유** — exit code로 판단한다는
  걸 배웠으니, 그걸 아무 데나 쓰면 안 되는 이유까지 말할 수 있어야 한다.

## 내 말로 3줄 요약

1. Bash는 명령어 통합 접착제이며 판단은 exit code로 한다: 문자열 중심의 언어로,
   `if` 문은 조건문이 아니라 명령어의 성공 여부(exit code `0`)를 검사해 흐름을 제어한다.
2. shebang과 실행 권한(`x`)은 명시하고 변수는 항상 따옴표로 감싼다: 단어 분리로 인한
   오동작과 `rm` 사고를 막기 위해 `"$VAR"`로 감싸야 하며, 파싱은 기계용 출력(`df -P`)이 안전하다.
3. exit code는 프로세스와 외부 세계(systemd, K8s) 간 핵심 신호다: 재시작으로 해결되지
   않는 문제를 livenessProbe에 걸면 CrashLoopBackOff 같은 불필요한 장애가 생기므로,
   probe 대상은 자동 복구 가능 여부를 기준으로 엄격히 판단해야 한다.
