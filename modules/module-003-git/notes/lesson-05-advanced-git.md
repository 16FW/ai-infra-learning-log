# Lesson 05. Advanced Git

## 핵심 개념
- 되돌리기는 세 가지다: `reset`(브랜치 포인터를 과거로, 이력을 되감음), `revert`(취소 커밋을 추가, 이력 보존), `reflog`(HEAD가 거쳐 온 위치의 기록, 안전망).
- push 전 커밋은 `reset`, 이미 공유한 커밋은 `revert`.
- `stash`는 미커밋 수정을 임시 보관, `clean`은 untracked 파일 삭제(복구 불가), `cherry-pick`은 커밋 하나의 변경분을 재적용, `rebase -i`는 push 전 커밋을 정리.
- `bisect`는 good/bad 사이를 이진 탐색해 문제의 첫 커밋을 찾는다. `submodule`은 다른 저장소를 특정 커밋으로 고정해 품는다.

## 동작 원리
- `reset`: `--soft`는 브랜치 포인터만, `--mixed`(기본)는 포인터+index, `--hard`는 포인터+index+작업 디렉터리를 대상 커밋에 맞춘다. `--hard`는 저장된 적 없는 수정을 잃는다.
- reset으로 이력에서 빠진 커밋 객체도 지워지지 않고 reflog가 붙잡고 있다. `git branch -d`는 조상 관계(merged 여부)로 판단하고 `-D`는 강제 삭제다. 객체는 reflog 만료와 gc 전까지 남는다.
- `stash`는 커밋 객체로 저장된다. parent 2개(보관 당시 HEAD, index 상태). 기본은 untracked를 보관하지 않고 `-u`가 필요하다.
- `clean`은 `-n`으로 미리 보기부터 한다. `-x`는 ignored 파일까지 지운다.
- `cherry-pick`과 `rebase`는 부모 대비 변경분을 새 부모 위에 재적용해 새 커밋을 만든다. author는 유지되고 committer, parent, tree가 달라진다.
- `rebase -i`: 처음 바뀐 커밋부터 뒤의 모든 커밋 해시가 바뀐다(해시 사슬). 이미 push한 커밋에 하면 팀원의 이력과 갈라진다.
- `bisect run`은 검사 명령의 종료 코드로 판정한다: 0=good, 1~127(125 제외)=bad, 125=skip, 128 이상=중단. 검사 스크립트가 틀리면 틀린 결과가 조용히 나온다 (`grep -q ok`가 `broken`에도 일치하는 사고). 알려진 good/bad에 먼저 돌려 검증하고, 줄 전체 일치는 `grep -x`.
- submodule: 부모 tree에 모드 `160000`(gitlink)으로 커밋 해시를 저장하고, `.gitmodules`에 경로와 URL을 둔다. 하위의 `.git`은 파일이며 `gitdir:`로 실제 데이터(`.git/modules/`)를 가리킨다. clone만 하면 비어 있으므로 `--recurse-submodules` 또는 `submodule update --init`이 필요하다.
- `--force-with-lease`는 마지막으로 본 원격 상태(`origin/*` 기록)와 같을 때만 덮어쓴다. fetch한 뒤에는 동료의 커밋을 내 이력에 통합하지 않았어도 통과하므로, 통합한 뒤 push하고 `--force-if-includes`를 함께 쓴다.

## 실습에서 한 것
- reset 세 모드의 결과를 예측표로 비교하고, reflog로 reset 이전 위치를 찾아 복구.
- 실수로 만든 비밀 키 커밋을 reset으로 정리하고, 브랜치를 지워도 객체가 reflog에 남는 것을 확인.
- stash 내부 구조 확인, clean 미리 보기, cherry-pick으로 hotfix 이식, rebase -i로 커밋 4개를 2개로 정리.
- 12개 커밋에서 bisect(수동, 자동)로 버그 커밋 탐색. 검사 스크립트의 오탐을 정답 파일과 비교해 발견하고 수정.
- submodule 추가, 버전 갱신, clone 후 초기화.
- bare 저장소에서 amend 후 push 거부, `--force-with-lease`의 stale 거부, `--force`로 동료 커밋이 사라지는 것과 중복 이력을 재현.

## Infrastructure 연결
- 배포 롤백은 문제 커밋을 `revert`하고 merge하는 방식이 이력을 보존해 안전하다 (GitOps).
- "어제까지 정상이던 배포가 오늘 깨졌다"는 `bisect run`에 `helm lint`나 테스트를 걸어 원인 커밋을 자동으로 찾는다.
- 비밀이 push됐다면 이력 정리보다 키 폐기가 먼저다.
- 공유 설정이나 모듈은 submodule, Terraform 모듈의 버전/커밋 고정 등으로 재현성을 확보한다.

## 면접 포인트
- reset(이력 되감기)과 revert(취소 커밋 추가)의 선택 기준은 이미 공유했는가이다.
- 공유된 이력의 rebase는 피하고, 불가피하면 합의와 복구 계획, force-with-lease 사용.
- bisect를 쓰기 전에 검사 스크립트부터 검증한다.

## 내 말로 3줄 요약
1. 되돌릴 때는 공유 전이면 reset, 공유 후면 revert를 쓰고, 실수로 놓친 커밋은 reflog로 찾되 Git에 저장한 적 없는 변경은 복구가 어렵다는 점을 기억한다.
2. stash로 작업을 보관하고, clean은 미리 확인한 뒤 실행하며, cherry-pick으로 필요한 변경만 가져오고 rebase -i로 공유 전 이력을 정리한다.
3. 버그는 검증된 테스트와 bisect로 찾고, 의존성은 submodule로 버전을 고정하며, 공유 이력은 함부로 재작성하지 않고 --force-with-lease도 만능 안전장치는 아님을 기억한다.
