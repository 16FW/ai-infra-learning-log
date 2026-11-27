# Lesson 7. 도커 모범 사례 및 보안

## 핵심 개념
- 보안 설정은 "컨테이너가 뚫려도 피해를 줄이는" 겹겹의 방어다. 컨테이너는 호스트 커널을 공유하므로 완전한 격리는 아니다.
- 비 root 실행(`USER`), 읽기 전용 파일시스템(`--read-only`), 권한 축소(`--cap-drop ALL`, `no-new-privileges`), 버전 고정, 작은 베이스 이미지와 `.dockerignore`, `HEALTHCHECK`.
- 비밀은 이미지에 굽지 않는다. 빌드에는 `--mount=type=secret`, 실행에는 파일 마운트나 시크릿 매니저를 쓰고, 새면 비밀을 교체(rotate)한다.

## 동작 원리
- 파일 권한(누가)과 마운트 모드(어디에)는 별개의 층이다. `--read-only`에서는 소유자가 `app`이어도 쓰기가 막힌다.
- `ENV`는 `docker inspect`의 `Config.Env`에, `ARG`는 `docker history --no-trunc`에서 이후 `RUN` 줄에 남는다.
- `COPY .env` 뒤에 `RUN rm .env`를 해도 `rm`은 whiteout만 추가하므로 COPY 레이어에 파일이 남는다(`docker save`로 확인).
- `-e`로 넣은 값은 컨테이너 설정에만 있고 이미지에는 없다.

## 실습에서 한 것
- 비 root: `useradd --system`으로 만든 사용자가 uid=999(app)였다. root 소유 `/app`에는 쓰기가 거부됐고, `--chown`한 `/app/app`에는 쓰기가 됐다. `HEALTHCHECK`가 있어 4초에는 `starting`, 10초에는 `healthy`였다.
- 읽기 전용: `--read-only`만으로도 앱은 기동했고 `/tmp` 쓰기는 실패했다. `--tmpfs /tmp`를 추가하자 성공했고, `/app/app`에는 소유자가 `app`이어도 `Read-only file system`이었다. `--cap-drop ALL --security-opt no-new-privileges`를 더해도 앱은 정상 기동했다.
- 비밀 노출: `ENV`, `ARG`, `COPY`+`rm`한 `.env` 모두 이미지를 가진 사람이 볼 수 있었고, 실행 시 `-e` 값은 이미지에 없었다(가짜 값으로 실험).

## Infrastructure 연결
- `USER`, `--read-only`, `--cap-drop`은 Kubernetes `securityContext`(`runAsNonRoot`, `readOnlyRootFilesystem`, `capabilities.drop`)와 거의 1:1로 이어진다.
- 시크릿은 Kubernetes Secret이나 AWS Secrets Manager 같은 외부 매니저로 주입하고, 이미지와 Git에는 넣지 않는다. CI에서는 이미지 스캔과 버전 고정을 배포 전 게이트로 둔다.

## 면접 포인트
- 이미지에 비밀이 들어간 게 확인되면, 레이어를 지우는 게 아니라 그 비밀을 즉시 교체(rotate)한다.

## 내 말로 3줄 요약
1. 컨테이너는 커널을 공유하므로 비 root, `--read-only`, `--cap-drop` 같은 설정으로 뚫렸을 때의 피해 범위를 줄여야 한다.
2. 비밀은 `ENV`, `ARG`, `COPY`+`rm` 모두 이미지에 남으므로 빌드에는 `--mount=type=secret`, 실행에는 마운트나 시크릿 매니저를 쓰고, 새면 교체한다.
3. 적용 순서는 "되돌릴 수 없는 피해 × 적용 비용"으로 정하고, 비밀 제거와 비 root부터 한다.
