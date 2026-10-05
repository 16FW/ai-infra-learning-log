# Lesson 04 — systemd와 로그

## 핵심 개념

### 왜 필요한가

터미널에서 띄운 프로세스는 터미널에 묶여 있다. SSH로 접속해 서비스를 띄우고
로그아웃하면 같이 죽는다. "터미널과 무관하게, 부팅 시 자동으로, 죽으면 다시
살아나는" 실행 방식이 필요하고, 그걸 담당하는 게 init 시스템 = systemd.

Docker, kubelet, containerd — 이것들 자체가 systemd 서비스다.
"K8s 노드가 NotReady"면 대부분 `systemctl status kubelet`부터 본다.

### 명령형이 아니라 선언형

직접 `python3 app.py &`로 띄우면 **내가 관리자**다. 죽으면 살리고, 재부팅 후
다시 띄우고, 로그도 직접 리다이렉트해야 한다.

systemd에 맡기면 **선언만 한다**:

```
"이 명령으로 실행해라"
"죽으면 5초 뒤 다시 띄워라"
"부팅할 때 자동으로 시작해라"
"이 사용자 권한으로 돌려라"
"메모리를 2GB 넘게 쓰면 죽여라"
```

이 사고방식이 그대로 Kubernetes로 이어진다. Pod YAML의 `restartPolicy`,
`resources.limits`가 정확히 같은 발상이다.

> systemd는 단일 서버판 Kubernetes다.

### 유닛 파일의 위치와 우선순위

```
/usr/lib/systemd/system/   패키지가 제공 (건드리지 않음)
/etc/systemd/system/       관리자 설정 (직접 만드는 곳, 우선순위 높음)
/run/systemd/system/       런타임 생성 (재부팅 시 소멸)
```

같은 이름의 유닛이 여러 곳에 있으면 `/etc`가 이긴다.
**패키지 기본값을 덮어쓰는 표준 방식.** (Lesson 1의 `/usr` vs `/etc` 구분)

### enable은 심볼릭 링크 생성이다

```
systemctl enable nginx
  → /etc/systemd/system/multi-user.target.wants/nginx.service
      -> /usr/lib/systemd/system/nginx.service
```

`disable`은 그 링크를 지우는 것뿐. 부팅 시 systemd가 `*.wants/` 디렉토리를
읽어서 시작 대상을 결정한다.

`enable`과 `start`는 **독립적**이다. `enable`만 하면 지금은 안 돌고 다음
부팅부터 돌고, `start`만 하면 지금은 돌지만 재부팅하면 안 뜬다.
합치려면 `systemctl enable --now`.

### journal — 구조화된 로그

```
텍스트 로그 (/var/log/syslog)   grep으로 뒤짐
journal (journalctl)            유닛별/시간별/우선순위별 필터링
```

각 로그 줄에 메타데이터(어느 서비스, PID, 우선순위)가 붙어 있어서 `grep` 대신
조건 질의를 한다. Module 009의 구조화 로깅(structured logging) 예고편.

systemd 서비스는 터미널이 없으므로, systemd가 프로세스의 **stdout/stderr를
파이프로 가로채서** journald에 넘긴다 (`StandardOutput=journal`이 기본값).
Lesson 1의 두 출구가 여기서 다시 쓰이고, `journalctl -p err`로 에러만 뽑을 수 있다.

## 동작 원리

### cgroup으로 프로세스 그룹을 관리한다

systemd는 PID 하나만 추적하는 게 아니라 cgroup으로 프로세스 그룹 전체를 묶는다.
그래서 자식 프로세스를 여럿 만드는 서비스도 `systemctl stop` 한 번에 전부
정리된다. `systemctl status` 출력 아래쪽 `CGroup:` 섹션에서 확인 가능.

**이 cgroup이 Docker 컨테이너 리소스 제한과 같은 커널 기능이다.**

### Type과 Restart

| Type | 의미 |
|---|---|
| `simple` | 프로세스가 계속 살아있어야 함 (기본값) |
| `oneshot` | 한 번 실행하고 끝나는 작업 |

`Type=simple`인데 프로세스가 끝나면 systemd는 실패로 판단한다.
한 번 실행하고 끝나는 작업은 `Type=oneshot`으로 **선언**해야
정상 종료가 `Deactivated successfully`로 처리된다.

`Restart=always`만 걸면 크래시 루프가 생긴다. 설정 오류로 앱이 시작 즉시 죽으면
초당 수십 번 재시작을 시도하며 CPU를 태운다.

```ini
Restart=always
RestartSec=5               # 재시작 전 대기
StartLimitBurst=5          # 5회 실패하면
StartLimitIntervalSec=60   # 60초 내에 → 포기
```

K8s의 `CrashLoopBackOff`가 같은 문제를 같은 방식(backoff)으로 해결한 것.

### Timer vs 스크립트 내부 루프

| | `while True: sleep(60)` | systemd Timer |
|---|---|---|
| 주기 변경 | 코드 수정 + 재배포 | 유닛 파일만 수정 |
| 실행 이력 | 직접 로깅 | `systemctl list-timers` |
| 스크립트가 멈추면 | 타이머도 멈춤 | Timer는 살아있음 |
| 역할 | 스크립트가 스케줄링까지 담당 | 스크립트는 한 가지만 |

**"무엇을 할지"와 "언제 할지"의 분리.** Airflow(Module 009)의 설계 철학과 같다
— DAG는 작업 정의, Scheduler는 실행 시점.

cron 대신 Timer를 쓰는 이유도 같다. cron은 로그가 따로 놀고 실패해도 조용하지만,
Timer는 journal에 통합되고 `systemctl status`로 마지막 실행 결과를 볼 수 있다.

Timer + oneshot 조합에서는 `Restart`가 필요 없다. 이번에 실패해도 다음 주기에
다시 실행되기 때문.

## 실습에서 한 것

Module 001의 `Lesson01.py`를 60초 주기 서비스로 등록했다.

```ini
# /etc/systemd/system/infracheck.service
[Unit]
Description=Lesson01 Infra Check Service

[Service]
Type=oneshot
User=eunho
ExecStart=/usr/bin/python3 /home/eunho/my-new-study/Module01/Lesson01.py
```

```ini
# /etc/systemd/system/infracheck.timer
[Unit]
Description=Run Lesson01 Infra Check every 60 seconds

[Timer]
OnBootSec=1min
OnUnitActiveSec=60s
Unit=infracheck.service

[Install]
WantedBy=timers.target
```

확인된 것:
- `print()` 출력이 journald로 수집됨
- 실행마다 PID가 바뀜 → Timer가 매번 새 프로세스를 띄움
- `Deactivated successfully` → `Type=oneshot` 덕분에 정상 종료로 처리
- `systemctl list-timers`로 `NEXT`/`LAST` 확인

`User=`를 지정하지 않으면 root로 돈다. 디스크 조회만 하는 스크립트에 root는
불필요하므로 `User=eunho`를 추가했다 (최소 권한 원칙).

**주의**: Python은 출력이 터미널이 아닐 때 버퍼링한다. 로그가 즉시 안 보이면
`PYTHONUNBUFFERED=1` 또는 `python3 -u`.

### 트러블슈팅 순서

1. `systemctl status <서비스>` — 상태와 `status=` 코드 확인
2. `systemd-analyze verify <유닛파일>` — 문법 오류
3. `journalctl -u <서비스>` — 로그 분석
4. `ExecStart` 명령을 **수동으로 실행** — systemd 문제인지 앱 문제인지 분리
5. `systemctl cat <서비스>` — systemd가 실제 로드한 내용 확인
   (daemon-reload 누락으로 "고친 파일과 실행되는 파일이 다른" 상황을 잡아낸다)

## Infrastructure 연결

| systemd | Kubernetes |
|---|---|
| Service (상주) | Deployment |
| Timer + oneshot | CronJob |
| `Restart=always` | `restartPolicy: Always` |
| `MemoryMax=2G` | `resources.limits.memory` |
| `journalctl -u` | `kubectl logs` |
| cgroup | cgroup (같은 커널 기능) |

### 이 서비스의 한계와 개선 방향

지금 만든 것은 모니터링 시스템이 아니라 **모니터링 시스템의 씨앗**이다.

| 한계 | 개선 |
|---|---|
| 서버가 죽으면 journal도 못 봄 | 중앙 집중식 로깅 (Loki, ELK) |
| 90%를 넘어도 아무도 모름 | 임계치 규칙 + 알림 (Prometheus + Alertmanager) |
| 서버 100대면 개별 관리 불가 | 표준 형식으로 노출 → 중앙에서 수집 |

```
각 서버: /metrics 로 값 노출 (node_exporter)
   ↓ 중앙이 주기적으로 긁어감 (pull)
Prometheus: 시계열 DB 저장 + 임계치 규칙 평가
   ↓ 규칙 위반 시
Alertmanager: Slack/PagerDuty
   ↓ 별도 경로
Loki / ELK: 로그 중앙 수집
   ↓
Grafana: 대시보드
```

Prometheus가 push가 아닌 **pull**을 택한 이유: push면 "안 보내는 건지 죽은 건지"
구분이 어렵지만, pull이면 중앙이 대상 목록을 알고 있어 응답 없는 서버를 즉시
특정할 수 있다.

알림 설계에서 주의할 것: 디스크가 90.1%와 89.9%를 오가면 알림이 수십 번 울린다.
그래서 "5분간 연속 90% 초과"처럼 지속 조건을 건다 (Prometheus `for: 5m`).
알림이 너무 많으면 사람이 무시하게 된다(alert fatigue).

## 면접 포인트

- `systemctl enable`은 `*.wants/`에 심볼릭 링크를 만드는 것이다.
- `enable`과 `start`는 독립적이다.
- 서비스가 `failed`일 때 `status=` 값으로 방향을 좁힌다
  (126=실행 권한, 127=명령 없음, 203=shebang/실행 형식, SIGKILL=OOM 등).
- "무엇을 할지"와 "언제 할지"를 분리하는 이유.

## 내 말로 3줄 요약

1. systemd는 백그라운드 관리와 부팅 자동화를 담당한다: 프로세스를 터미널 독립적으로
   관리하며, Kubernetes처럼 선언형 방식과 cgroup을 통해 프로세스 그룹을 통제한다.
2. 단순 스케줄링 및 1회성 작업엔 Timer + oneshot을 쓴다: cron과 달리 실패가 조용히
   묻히지 않고 journald 로그에 통합되며, `systemctl status`로 상태와 이력을 추적할 수 있다.
3. `enable`과 `start`는 독립적이며 심볼릭 링크로 동작한다: 부팅 시 자동 실행은
   `enable`(`*.wants/`에 링크 생성), 즉시 실행은 `start`를 쓰며, 트러블슈팅은
   `status` → `journalctl` → `systemd-analyze` 순으로 확인한다.
