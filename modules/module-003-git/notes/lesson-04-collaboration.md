# Lesson 04. 협업 워크플로우 (PR, merge 전략, hooks)

## 핵심 개념
- Pull Request는 Git이 아니라 **GitHub의 기능**이다. Git은 브랜치와 merge만 안다. PR은 요청 + 리뷰 + CI 검사 + 승인을 한곳에 모은 main 앞의 검문소.
- merge 전략은 PR을 합칠 때 이력을 어떤 모양으로 남길지에 대한 선택이다.
- git hook은 commit/push 같은 동작 전후에 실행되는 스크립트이고, 종료 코드가 0이 아니면 동작이 중단된다.

## 동작 원리
- 세 가지 merge 방식 (같은 PR, 커밋 2개 기준):
  - Merge commit: 부모 2개인 merge commit 추가. PR 커밋 해시가 main에 **그대로** 남는다.
  - Squash and merge: 커밋 1개로 압축. 부모는 이전 main 끝이라 PR 커밋 해시는 main에 없다.
  - Rebase and merge: 커밋 2개를 새로 만들어 일직선으로 이음. 부모가 바뀌므로 해시가 다르다.
- `git merge-base --is-ancestor <커밋> main` 종료 코드로 확인: merge commit PR은 0(조상), squash/rebase PR은 1.
  그래서 squash/rebase로 합친 브랜치는 `git branch --merged main`에 안 나온다.
- `git pull --rebase`는 push하지 않은 내 커밋을 fetch한 원격 끝 위에 다시 적용한다.
  재생성된 커밋은 tree(새 부모가 가진 파일 반영), parent, committer 시각이 바뀌고 author는 유지된다.
  옛 커밋 객체는 지워지지 않고 남아 있다.
- hook은 `.git/hooks/`에 있어서 추적 대상이 아니므로 clone으로 전달되지 않는다.
  공유하려면 `core.hooksPath`로 레포 안의 폴더를 지정하거나 pre-commit 프레임워크를 쓴다. 둘 다 각자 설치 명령이 필요하다.
- `--no-verify`로 hook을 우회할 수 있으므로 우회 불가능한 방어선은 서버 쪽(CI 필수 검사, branch protection, secret scanning)이다.

## 실습에서 한 것
- 브랜치 3개로 PR을 만들어 세 가지 merge 방식을 각각 적용하고, 사전에 기록한 PR 커밋 해시와 main 이력을 비교.
- 로컬 커밋 2개 + 원격 1개로 갈라진 상태에서 `pull --rebase`로 일직선 이력을 만들고 `cat-file`로 옛 커밋과 새 커밋의 차이를 확인.
- pre-commit hook으로 AWS 키 패턴 차단(exit 1), 정상 커밋 통과(exit 0), `--no-verify` 우회를 직접 테스트.

## Infrastructure 연결
- 인프라 변경(Terraform, K8s YAML)도 PR을 거친다. PR에서 CI(`terraform plan`, `helm lint`, secret scan)가 돌고 승인된 변경만 main에 들어가 배포로 이어진다 (GitOps).
- 로컬 hook은 개인의 1차 방어선, 서버 쪽 검사는 우회할 수 없는 방어선이다.

## 면접 포인트
- PR은 GitHub의 기능이고, 팀이 squash를 기본으로 쓰는 이유는 main을 기능 단위로 깔끔하게 유지하고 revert를 쉽게 하기 위해서다 (단점: 세부 이력 소실).
- 비밀이 push되면 이력 정리보다 키 폐기가 먼저다.

## 내 말로 3줄 요약
1. PR은 GitHub에서 코드 리뷰와 CI 검사를 거쳐 안전하게 병합하기 위한 협업 절차이며, merge 전략에 따라 main 브랜치에 남는 커밋 이력과 해시가 달라진다.
2. `git pull --rebase`는 로컬 커밋을 최신 원격 커밋 위에 재적용해 선형적인 이력을 만들며, 부모가 바뀌기 때문에 새로운 커밋이 생성된다.
3. pre-commit hook은 커밋 전 실수를 막는 1차 방어선이지만 우회할 수 있으므로, CI와 Branch Protection을 함께 적용해 원격에서도 검증해야 한다.
