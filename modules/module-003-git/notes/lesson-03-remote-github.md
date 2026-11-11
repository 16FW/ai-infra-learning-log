# Lesson 03. Remote & GitHub

## 핵심 개념
- remote는 다른 저장소의 **이름 붙은 URL**이다 (보통 `origin`).
- `origin/main`(remote-tracking branch)은 "마지막으로 통신했을 때 원격 main이 어디 있었나"를 적어 둔 **로컬 기록**이다. 실체는 `.git/refs/remotes/origin/main` 파일.
- `origin/main`은 실시간이 아니다. fetch나 push를 해야만 갱신된다.
- upstream은 로컬 브랜치와 원격 브랜치의 연결이고 `.git/config`의 `[branch "main"]`(`remote`, `merge`)에 기록된다.

## 동작 원리
- `clone` = 객체 복사 + `origin` 등록 + `origin/*` 생성 + 로컬 브랜치 생성.
  빈 저장소를 clone하면 `origin/main`은 아직 존재하지 않는다 (가리킬 커밋이 없어서).
- `fetch`: 새 객체를 받고 **`origin/*`만 갱신**. 로컬 `main`과 작업 디렉터리는 그대로.
- `pull` = `fetch` + upstream 브랜치를 현재 브랜치에 merge.
- `push`: 새 객체를 원격 `objects`로 보내고, 원격의 `refs/heads/main`을 이동시킨다. 성공하면 내 `origin/main`도 갱신된다.
- push가 거부되는 이유(`rejected ... fetch first`): 원격 브랜치가 내 브랜치의 **조상이 아니면** FF가 불가능하기 때문. 해결은 fetch → merge → push. `--force`는 동료의 커밋을 이력에서 지울 수 있다.
- `status`의 "up to date"는 원격의 현재 상태 확인이 아니라 **마지막 통신 시점의 `origin/main`과 같다**는 뜻이다.
- `ls-remote`는 객체를 받지 않고 원격의 ref 목록만 조회한다.
- bare 저장소는 작업 디렉터리 없이 `HEAD`, `objects`, `refs`만 있는 서버용 저장소이고, GitHub의 기본 구조와 같다.

## 실습에서 한 것
- GitHub 빈 repo를 두 곳(`clone-a`, `clone-b`)에 clone해 두 협업자를 흉내 냄.
- `clone-b`가 push한 뒤 `clone-a`에서 `status` → `fetch` → `status` → `merge`로 `origin/main`의 이동과 FF merge 관찰.
- 양쪽이 각자 커밋해 갈라진 이력에서 push 거부를 재현하고, fetch + merge + push로 해결 (merge commit의 `^1`=내 쪽, `^2`=합쳐 들어온 쪽).
- `.git/config`의 upstream 설정과 `git branch -vv`의 `[origin/main]` 표시 확인.

## Infrastructure 연결
- GitHub `main`은 single source of truth이고, push 이벤트가 CI/CD를 시작시킨다.
- CI 스크립트에서 `fetch` 없이 `origin/main`과 비교하면 틀린 결과가 나올 수 있다.
- 원격의 상태가 곧 배포되어야 할 상태가 되는 GitOps의 기반.

## 면접 포인트
- `origin/main`은 마지막 통신 시점의 스냅샷이고 실시간이 아니다.
- push 거부는 non-fast-forward 보호이며 `--force` 대신 fetch + merge로 푼다 (꼭 필요하면 `--force-with-lease`).

## 내 말로 3줄 요약
1. Git의 remote는 원격 저장소를 가리키는 이름이며, `origin/main`은 마지막으로 통신했을 때의 원격 브랜치 상태를 로컬에 기록한 것이다.
2. `fetch`, `pull`, `push`는 각각 원격 정보 가져오기, 로컬 브랜치와 병합하기, 로컬 커밋을 원격에 반영하기 위한 작업이다.
3. 협업 중 push가 거부되면 원격과 로컬의 이력이 달라졌다는 의미이므로, `fetch → merge → push` 순서로 이력을 동기화해야 한다.

