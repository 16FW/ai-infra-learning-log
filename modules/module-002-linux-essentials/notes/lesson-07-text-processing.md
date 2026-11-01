# Lesson 07 — 텍스트 처리와 로그 분석

## 핵심 개념

### 세 도구의 역할

```
grep  →  줄을 "고른다"      (필터)
sed   →  줄을 "고친다"      (치환)
awk   →  줄을 "쪼개서 센다" (열 단위 처리 + 계산)
```

각 도구는 단순하지만 파이프로 엮으면 조립 라인이 된다.

```bash
awk '$8 == 500 {print $6}' access.log | sort | uniq -c | sort -rn
# 500 에러 → URL 열만 → 정렬 → 세기 → 많은 순
```

### awk의 모델

입력을 한 줄씩 읽어 **공백 기준으로 쪼개** `$1`, `$2`, ...에 넣는다.
`$0`은 줄 전체, `$NF`는 마지막 필드, `NR`은 지금까지 읽은 줄 수.

Lesson 5에서 쓴 `awk '{print $5}'`가 `df` 출력의 다섯 번째 열(Use%)을 뽑던 것이
이 모델이다.

### 필드 번호는 추측하지 않고 찍어본다

```bash
head -1 access.log | awk '{for(i=1;i<=NF;i++) print i": "$i}'
```

따옴표로 묶인 `"GET /api/predict HTTP/1.1"`도 awk는 공백으로만 쪼갠다.
`"GET`, `/api/predict`, `HTTP/1.1"`이 각각 별개 필드다. 이번 실습에서 필드 번호를
잘못 세서 상태 코드 자리에 **응답 크기**가 나왔다.

> 결과가 8종류로 나온 시점에서 이상 신호였다. 상태 코드라면 200, 500, 503 정도만 나온다.

### 집계 관용구

```bash
awk '{print $1}' access.log | sort | uniq -c | sort -rn
```

- `uniq -c`는 **인접한 줄만** 비교한다. 정렬 안 된 입력이면 같은 값이 떨어져 있을 때
  별개 그룹으로 센다. **에러 없이 틀린 숫자가 나온다.**
- 마지막 `sort -rn`이 있어야 "가장 많은 순"이다. (`-n` 숫자, `-r` 내림차순)

## 동작 원리

### 위치로 특정하는 것이 문자열 패턴보다 안정적이다

```bash
grep -c '500' access.log          # 응답 크기 500, URL의 v500 등에도 걸림
grep -c '" 500 ' access.log       # 경계를 만들었지만 형식이 바뀌면 깨짐
awk '$8 == 500' access.log        # 상태 코드 필드만 비교
```

### 평균은 거짓말을 한다

```
전체 평균 응답 시간:     0.8466초
/api/predict 평균:      1.19914초
1초 초과 요청:           전부 /api/predict
에러(500/503) 3건:       전부 /api/predict
```

전체 평균은 빠른 `/health` 요청에 희석되어 문제를 숨긴다. 엔드포인트별로 쪼개야
범인이 보인다. 실무에서는 평균 대신 **p95, p99** 백분위수를 본다. 평균이 멀쩡해도
p99가 10초면 100명 중 1명은 10초를 기다린다.

### 집계 결과가 "그럴듯하면" 의심한다

0건 집계는 `division by zero`로 드러나지만, 잘못된 필터로 3건만 잡힌 집계는 정상처럼
보인다. 방어 코드:

```bash
awk '... END { if (count > 0) print sum/count; else print "no match" }'
```

### 필터링은 데이터 소스에 가까운 쪽에서 한다

```bash
journalctl -u infracheck | grep "10:"                       # 텍스트 "10:"이 든 모든 줄
journalctl -u infracheck --since "1 hour ago"               # 타임스탬프 메타데이터 비교
```

- `grep`은 시간을 이해하지 못한다. `20:10:33`도, 메시지 본문의 `10:`도 걸린다.
- `--since`는 처음부터 범위만 읽는다. 로그가 수백만 건이면 전체를 꺼내 텍스트로 바꾼 뒤
  버리는 방식과 차이가 크다.

SQL의 `WHERE`, `kubectl get pods -l app=api`, Prometheus의 레이블 필터가 같은 원칙이다.

## 실습에서 한 것

액세스 로그 10줄로 8종 질의:

| 질의 | 사용한 것 |
|---|---|
| 상태 코드별 건수 | `awk '{print $8}' \| sort \| uniq -c` |
| `/health` 제외 | `grep -v '/health'` |
| IP별 건수 순위 | `awk '{print $1}' \| sort \| uniq -c \| sort -rn` |
| 1초 초과 요청 | `awk '$NF > 1 {print $6, $NF}'` |
| 전체 평균 응답 시간 | `awk '{sum+=$NF} END {print sum/NR}'` |
| 엔드포인트별 평균 | `awk '$6 == "/api/predict" {sum+=$NF; count++} END {...}'` |

실제 journal에서 `infracheck.service` 분석:

```bash
journalctl -u infracheck.service --no-pager | grep -c '"os": "Linux"'          # 3207
journalctl -u infracheck.service --no-pager | grep '"error":' | grep -v 'null' # 비어 있음
```

3207번 실행되는 동안 실패 0건. "에러가 있는 줄"을 찾는 대신 **"에러 필드가 null이
아닌 줄"**을 찾았다. Module 001에서 JSON 스키마를 고정해 둔 덕분에 `grep` 한 줄로
집계가 된다.

더 안정적인 지표는 애플리케이션 출력이 아니라 systemd 자신이 남기는 줄이다:

```bash
journalctl -u infracheck.service -q --no-pager | grep -c "Finished infracheck"
```

### 발견: 최근 1시간 실행 0건

`--since "1 hour ago"`로 세어 보니 0건이었다. 전체로는 3207번이 돌았으므로 어딘가에서
멈춘 것이다. WSL은 Windows를 재부팅하거나 WSL을 종료하면 리눅스 전체가 꺼진다.
`[Install] WantedBy=`가 있어도 **`enable`을 하지 않았다면** 다음 부팅에서 타이머가
살아나지 않는다. (Lesson 4: `enable`과 `start`는 독립적)

> 조용하다는 것이 정상이라는 뜻은 아니다. 감시자가 죽어 있을 수도 있다.
> 그래서 항상 발화하는 알림(Prometheus의 `Watchdog`)으로 **감시자를 감시**한다.

## Infrastructure 연결

- 구조화된 로그(고정된 JSON 스키마)는 질의가 쉽다. Module 009의 structured logging과
  Loki/ELK가 이 아이디어를 확장한다.
- 로그를 서버마다 SSH로 들어가 `grep`하면: 서버 간 로그를 시간순으로 합쳐 볼 수 없고,
  서버가 죽으면 로그도 같이 접근 불가이며, 50대에 접속하는 동안 장애는 계속 진행된다.
  → 중앙 집중식 로깅.
- p95/p99는 Prometheus 히스토그램 메트릭이 계산하기 위해 존재한다.

## 면접 포인트

- `sort | uniq -c`에서 `sort`를 빼면 **조용히 틀린 결과**가 나온다.
- "평균 응답 시간은 정상인데 사용자는 느리다고 한다" → 백분위수로 꼬리를 보고,
  엔드포인트 → 시간대 → 클라이언트 순으로 쪼갠다.
- `--since`가 `grep` 시간 필터보다 나은 이유(의미론 + 성능).
- 404 상위 URL 5개: `awk '$9 == 404 {print $7}' access.log | sort | uniq -c | sort -rn | head -5`

## 내 말로 3줄 요약

1. 도구 활용과 집계 원칙: grep(선택)·sed(치환)·awk(열 처리)는 파이프라인으로 조합해 사용하되, 오차 없는 분석을 위해 패턴 검색보다 위치(필드) 기반 추출 및 sort | uniq -c 정렬 순서를 엄격히 지킨다,

2. 분석 관점과 조회 효율성: 전체 평균은 특정 문제(지연/에러)를 희석하므로 엔드포인트별 분리와 백분위수(p95/p99) 조사가 필요하며, 텍스트 탐색(grep)보다 데이터 소스 단의 범위 필터링(--since)을 우선해야 한다.

3. 운영 전략과 감시 시스템: 구조화된 로그(JSON)와 중앙 집중식 로깅으로 파싱과 통합 조회를 용이하게 하고, 무응답이 정상을 뜻하진 않으므로 감시 시스템 자체(타이머/서비스 상태)도 모니터링해야 한다.
