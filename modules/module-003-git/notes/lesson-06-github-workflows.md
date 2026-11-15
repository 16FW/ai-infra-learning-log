# Lesson 06. GitHub Workflows (Issues, Actions, 보호 규칙, ML 프로젝트의 Git 운영)

## 핵심 개념
- Issue는 작업 단위 티켓이고, PR 본문의 `Closes #N`은 **기본 브랜치로 merge될 때** 이슈를 자동으로 닫는다.
- GitHub Actions는 Git 이벤트에 반응해 서버에서 도는 자동화다. workflow(`.github/workflows/*.yml`) → job(새 VM에서 실행) → step. step의 종료 코드가 0이 아니면 실패.
- CI는 "서버에서 도는 pre-commit hook"이다. 설치가 필요 없고 `--no-verify`로 우회할 수 없다.
- 실패한 CI가 merge를 막으려면 branch protection(repository rules)에서 **필수 상태 검사**로 지정해야 한다.

## 동작 원리
- `on`에 지정한 이벤트에만 실행된다. `pull_request`와 `push: branches: [main]`만 걸었다면 feature 브랜치를 push만 해서는 돌지 않고 PR을 열어야 돈다.
- `permissions: contents: read`로 최소 권한을 선언하고, `persist-credentials: false`로 토큰이 저장소 설정에 남지 않게 한다.
- `grep`의 종료 코드는 0=발견, 1=없음, 2=오류다. "발견하면 실패"로 쓸 때는 1과 2를 구분해야 검사 자체가 깨진 것을 놓치지 않는다.
- main 직접 push는 `GH013 Repository rule violations ... Changes must be made through a pull request`로 거부된다. Lesson 3의 `fetch first` 거부(FF 불가)와 달리 **정책 위반**이다.
- 큰 파일 실험(20MB 파일 3버전 + 삭제): `.git`은 gc 전 58M, gc 후 39M. 삭제 커밋은 이력의 blob을 지우지 않는다. 1~2바이트 수정은 delta로 압축되지만 재학습으로 바뀐 가중치는 압축이 안 되어 버전마다 풀사이즈로 쌓인다.
- Git LFS는 Git에 포인터 파일(sha256과 크기)을 두고 실제 파일은 LFS 저장소에 둔다. DVC는 `.dvc` 메타데이터(내용 해시)를 Git으로 관리하고 데이터는 캐시와 원격 저장소에 둔다.

## 실습에서 한 것
- Issue → 브랜치 → PR(`Closes #N`) → squash merge로 CONTRIBUTING.md와 PR 템플릿 추가.
- AWS 키 패턴 검사와 Python 문법 검사를 하는 CI 워크플로우 작성, 정상/가짜 키/문법 오류 세 가지 PR로 검증.
- main에 직접 push해 보호 규칙 거부를 확인하고, 백업 브랜치를 만든 뒤 로컬 main을 원격에 맞춰 정리.

## Infrastructure 연결
- PR마다 CI(lint, test, secret scan, 이후 `helm lint`, `terraform plan`)가 돌고 필수 검사와 승인을 통과한 변경만 main에 들어가 배포로 이어진다 (GitOps).
- 모델 가중치와 데이터는 Git이 아니라 DVC/LFS 같은 별도 저장소로 관리하고 Git에는 해시/포인터만 둔다 (Project 03).

## 면접 포인트
- CI는 우회할 수 없는 서버 쪽 검사지만, 실패가 merge를 막으려면 필수 상태 검사로 지정해야 한다.
- 큰 파일을 커밋하면 삭제해도 이력에 남으므로 이력 정리(filter-repo)와 재발 방지(.gitignore, 크기 검사, LFS/DVC)가 필요하다.

## ci.yml 핵심 줄 (내 말로)
- `else rc=$?` 블록이 필요한 이유:발견(0)과 오류(2)를 둘 다 실패로 잡아서, 검사가 고장 난 채로 통과하는 걸 막기 위해
- `persist-credentials: false`를 쓴 이유:검사만 하는 job에 저장소 쓰기용 토큰이 남아 있지 않게 해서, 다른 step이 토큰을 가져가거나 악용하지 못하게 하려고
- 초록불이 진짜 검사했다는 걸 확인한 방법:일부러 틀린 PR을 넣어서 빨간불이 뜨는지 봤다. 실패할 때 실패하는 검사여야 초록불을 믿을 수 있다

## 내 말로 3줄 요약
1. Issue로 할 일을 정하고 PR로 변경을 검토한 뒤, 기본 브랜치에 병합하면 Closes #N으로 관련 이슈까지 자동으로 닫을 수 있다.
2. Actions로 PR마다 자동 검사하고, 보호 규칙에서 필수 검사로 지정해야 CI가 실패한 변경의 병합을 막을 수 있다.
3. 큰 모델·데이터 파일은 삭제해도 Git 이력에 남으므로, LFS나 DVC로 따로 관리하고 Git에는 포인터나 메타데이터만 남긴다.
