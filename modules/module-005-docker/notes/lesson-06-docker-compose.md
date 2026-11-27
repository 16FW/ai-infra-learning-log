# Lesson 6. 도커 컴포즈

## 핵심 개념
- Compose는 여러 컨테이너로 이루어진 앱을 `compose.yaml` 하나에 선언하고 `docker compose up` 한 번으로 만들고 `down`으로 정리하는 도구다. 환경을 코드로 선언해서 누구나 같은 명령으로 재현한다.
- 지금까지 배운 것이 한 파일에 모인다: `build:`(이미지), `ports:`(포트 매핑), `volumes:`(데이터 보존), 자동 생성되는 네트워크(서비스 이름이 DNS 이름).
- `depends_on`은 시작 순서만 보장한다. 의존 서비스가 준비 완료인지는 `healthcheck`와 `condition: service_healthy`로 기다린다.

## 동작 원리
- `up`을 하면 `프로젝트이름_default` 네트워크가 자동으로 만들어지고, 서비스 이름(`redis`)이 이 네트워크 안에서 IP로 풀린다.
- `down`은 컨테이너와 네트워크를 지우지만 볼륨은 남기고, `down -v`는 볼륨(데이터)까지 지운다.
- `down`이 보내는 SIGTERM에 redis가 종료 직전 데이터를 저장해서, 재시작 뒤에도 카운트가 이어진다.
- "컨테이너가 시작됨"과 "요청을 받을 준비가 됨"은 다르다. `up --wait`는 `healthy`가 될 때까지 기다린다.

## 실습에서 한 것
- api(FastAPI) + redis + 볼륨 `hitsdata`를 `compose.yaml`로 묶었다. 네트워크 `lesson-06_default`와 볼륨 `lesson-06_hitsdata`가 자동으로 만들어졌고, api 컨테이너 안에서 `redis`가 `172.20.0.2`로 풀렸다. redis는 호스트에 포트를 열지 않았다.
- `up` 직후 바로 호출하면 `HTTP 000`이 났고, 시간이 지난 뒤에는 정상이었다(앱이 뜨기 전에 호출한 타이밍 문제로 추정).
- 영속성: `hits` 2 → `down` → `up` → 3(유지), `down -v` → `up` → 1(초기화).
- 헬스체크: `up --wait` 직후 `HTTP 200`(`hits` 1). redis를 `stop`해도 `/health`만 보는 api는 `healthy`였고 `/hits`는 500이었다.

## Infrastructure 연결
- Compose의 서비스 이름과 자동 네트워크는 Kubernetes Service DNS와 같은 발상이고, `compose.yaml`은 Kubernetes manifest의 로컬 버전이다.
- `service_healthy`, `up --wait`는 readiness/startup probe와 같은 문제를 푼다. liveness는 가볍게(재시작용), readiness는 모델 로드와 의존 서비스 연결까지(트래픽 제어용)로 나눈다. 로딩이 긴 모델 서버는 startup probe를 둔다.
- `down`과 `down -v`의 차이는 운영에서 데이터를 지우는 사고를 막는 습관이다.

## 면접 포인트
- "`depends_on`을 걸었는데도 api가 redis 연결 오류를 낸다"면 시작 순서와 준비 완료가 다르다는 점을 먼저 떠올리고 `healthcheck`와 `service_healthy`를 쓴다.

## 내 말로 3줄 요약
1. Compose는 여러 컨테이너의 이미지, 포트, 볼륨, 네트워크를 `compose.yaml` 하나로 선언해서 `up` 한 번으로 같은 환경을 재현하게 해 준다.
2. `depends_on`은 시작 순서만 보장하므로, 의존 서비스가 준비된 뒤에 시작하려면 `healthcheck`와 `condition: service_healthy`를 써야 하고, `down -v`는 볼륨까지 지우니 주의한다.
3. 헬스체크는 liveness(프로세스 생존, 가볍게)와 readiness(모델 로드와 의존 서비스까지)를 나눠야 연쇄 재시작을 피하면서 준비된 인스턴스에만 트래픽을 보낼 수 있다.
