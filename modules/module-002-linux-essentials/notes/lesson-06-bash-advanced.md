# Lesson 06 — Bash 스크립팅 심화 (안전장치와 trap)

## 핵심 개념

### Bash의 기본 동작은 위험하다

> 명령이 실패해도 스크립트는 다음 줄로 계속 간다.

```bash
cd /data/models        # 이 디렉토리가 없으면 에러 출력하고...
rm -rf *               # 그대로 실행된다
```

`cd`가 실패하면 현재 디렉토리가 그대로다. 그 상태에서 `rm -rf *`가 돌면
있던 곳이 전부 지워진다. Python이었다면 예외가 터지고 멈췄을 것이다.

그래서 스크립트 맨 위에 안전장치를 거는 게 관례가 됐다.

```bash
set -euo pipefail
```

| 옵션 | 이름 | 동작 |
|---|---|---|
| `-e` | errexit | 명령이 실패하면 즉시 중단 |
| `-u` | nounset | 정의되지 않은 변수를 쓰면 에러 |
| `-o pipefail` | | 파이프 중간이 실패해도 전체를 실패로 |

### set -e는 만능이 아니다

**"검사받는 위치"의 실패는 무시한다.**

```bash
if 명령; then ...      # 무시
명령 && 다른명령        # 왼쪽 실패는 무시
명령 || 대체명령        # 왼쪽 실패는 무시
! 명령                 # 무시
명령 | 다른명령         # pipefail 없으면 마지막 것만 봄
```

당연한 설계다. `if`가 실패를 검사하는 구문인데 실패할 때마다 죽으면 `if`를
쓸 수가 없다.

**실무 함정:**

```bash
set -e
backup_database && upload_to_s3     # backup이 실패해도 계속 감
echo "백업 완료"                     # 거짓말 출력
```

`&&` 뒤에 뭔가를 붙이는 순간 왼쪽은 보호 범위에서 빠진다.
중요한 명령은 명시적으로 검사한다:

```bash
if ! backup_database; then
    echo "백업 실패" >&2
    exit 1
fi
```

> `set -e`를 걸었다고 안심하면 안 된다.

### pipefail이 필요한 이유

```bash
USAGE=$(df -P "$PATH" | tail -1 | awk '{print $5}' | tr -d '%')
```

`df`가 실패해도 파이프라인의 exit code는 **마지막 명령(`tr`)의 것**이다.
`tr`은 빈 입력을 받아도 성공(0)하므로 `df`의 실패가 통째로 삼켜진다.

빈 값 검사(`[ -z "$USAGE" ]`)로 **증상**을 막을 수도 있지만, `pipefail`은
**원인 지점에서 바로 멈춘다.**

### set -u는 조용한 실패를 막는다

```
set -u 있음:  unbound variable → 즉시 중단, 변수 이름을 알려줌
set -u 없음:  빈 문자열로 치환 → 아무 일 없었던 듯 진행
```

```bash
BACKUP_DIR="/data/backups"
rm -rf "$BACKUP_DIRR/old"     # 오타(R 두 개) → rm -rf "/old"
```

더 흔한 경우는 **환경변수 누락**이다. 로컬 `.bashrc`에 있던 변수가 CI 환경이나
컨테이너 안에는 없다. 컨테이너는 환경변수로 설정을 주입받는 게 기본이라 누락이 잦다.

의도적으로 "없을 수도 있는" 변수는 기본값을 주면 통과한다:

```bash
LOG_LEVEL="${LOG_LEVEL:-info}"
```

### trap — Bash의 시그널 핸들러

```bash
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT     # 어떻게 끝나든 정리
```

Python의 `try/finally`와 같은 역할. 스크립트가 정상 종료하든, 에러로 죽든,
Ctrl+C를 받든 반드시 실행할 정리 작업을 등록한다.

trap에 등록하는 정리 작업은 **멱등(idempotent)해야** 한다. `rm -rf "$TMPDIR"`는
디렉토리가 이미 없어도 에러가 안 난다.

## 동작 원리

### trap도 SIGKILL은 못 막는다

Lesson 3의 규칙이 Bash에서도 그대로 성립한다.

```
정상 종료  → trap 실행 → 정리됨
Ctrl+C     → trap 실행 → 정리됨       (SIGINT는 가로챌 수 있음)
kill -9    → trap 건너뜀 → 쓰레기 남음  (커널이 직접 제거)
```

`trap`은 셸이 등록하는 핸들러이므로 셸이 실행될 기회를 얻어야 작동한다.
SIGKILL은 프로세스에 전달조차 되지 않는다.

**남는 "쓰레기"가 실제로 무엇인가:**
- 임시 파일, 캐시 디렉토리
- 락 파일(`.lock`) → **다음 실행이 "이미 실행 중"으로 착각해 실패**
- DB 커넥션 → 서버 쪽에 좀비로 남아 커넥션 풀 고갈
- 분산 락(Redis, etcd) → 다른 노드가 영원히 대기

세 번째가 특히 고약하다. `kill -9`로 죽인 프로세스의 락 파일 때문에 서비스가
재시작을 못 하는 상황이 실제로 생긴다.

### K8s 종료 흐름과 동일하다

```
SIGTERM (유예 30초) → trap/핸들러 실행 → 정리 → 정상 종료
                      ↓ 30초 내 안 끝나면
SIGKILL             → 정리 코드 실행 안 됨 → 쓰레기 남음
```

### 배열

```bash
PATHS=("$@")                      # 스크립트에 넘어온 모든 인자
echo "${#PATHS[@]}"               # 배열 길이 (# 이 개수)
for p in "${PATHS[@]}"; do ...    # 모든 요소 (따옴표 필수)
```

`"${PATHS[@]}"`의 따옴표가 없으면 공백 있는 경로가 쪼개진다 — Lesson 5의
단어 분리가 배열에서도 그대로 적용된다.

### exit과 return

- `exit` — 스크립트 전체 종료
- `return` — 함수만 종료

여러 대상을 순회하며 검사하려면 함수는 `return`을 써야 한다. 그리고 `set -e`
때문에 첫 실패에서 스크립트가 죽으므로, 호출을 `if`로 감싸 보호 범위에서 뺀다.

```bash
if ! check_single_path "$p"; then
    FAILED=1
fi
```

## 실습에서 한 것

- `set -e` 동작 비교: `false` 단독은 중단, `if false; then ... fi`는 계속 진행
  (존재하지 않는 명령 = exit 127 도 `if` 안에서는 무시됐다)
- `set -u` 유무 비교: `unbound variable` 중단 vs 빈 문자열 출력
- `trap` 3경우 검증: 정상 종료 / Ctrl+C / `kill -9`
- `disk-check.sh`에 배열과 반복문 적용 — 여러 경로를 한 번에 검사

**실행 중 발견**: `. script.sh`(source)로 실행했더니 `set -e`가 현재 셸에
적용되어 **bash 세션 자체가 종료**됐다. `./`와 `.`의 차이가 여기서 드러난다.

## Infrastructure 연결

- Dockerfile `RUN`, entrypoint 스크립트, GitHub Actions `run:`, K8s `command:` —
  앞으로 쓰게 될 Bash는 전부 "실패했는데 계속 진행하면 더 큰 사고가 나는" 자리다.
- 컨테이너 entrypoint에서 `set -u`는 환경변수 누락을 즉시 드러내 준다.
- `trap ... EXIT`는 컨테이너가 SIGTERM을 받았을 때 임시 자원을 정리하는
  Graceful Shutdown의 Bash 버전이다.

## 면접 포인트

- `set -euo pipefail`이 각각 무엇을 막는지, 그리고 `set -e`가 **무시하는 위치**가
  어디인지.
- `trap`이 SIGKILL에는 작동하지 않는 이유와, 그래서 남는 것들(락 파일 등).
- `source`와 `./`의 차이.

## 미완료

`getopts` 기반 옵션 파싱(`-p`, `-t`, `-h`)은 Module 002 마무리 시점에 재시도.

## 내 말로 3줄 요약

1. 안전한 스크립트의 기본은 `set -euo pipefail`이다: 에러 발생 시 즉시 중단(`-e`),
   미정의 변수 감지(`-u`), 파이프 중간 실패 감지(`-o pipefail`)를 통해 조용한 실패와
   2차 사고를 방지한다.
2. `trap`은 종료·예외 시 임시 자원을 정리하는 안전장치다: 정상 종료나 `SIGINT` 시
   락 파일, 임시 디렉토리 등을 비우는 멱등성(idempotent) 정리 로직을 등록할 때 쓴다.
3. `trap`과 시그널 핸들러도 `SIGKILL`(-9)은 막지 못한다: 커널이 프로세스에 기회를 주지
   않고 즉시 제거하므로 락 파일이나 캐시 쓰레기가 남을 수 있으며, `set -e`는 `if`나
   `&&` 등 조건 검사 영역의 실패를 무시하므로 주의해야 한다.
