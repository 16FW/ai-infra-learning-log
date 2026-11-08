# Lesson 02. Branch & Merge

## 핵심 개념
- branch는 **커밋 해시 하나가 적힌 작은 파일**(`.git/refs/heads/<name>`)이다. 복사가 아니다.
- HEAD는 "지금 어느 브랜치(또는 커밋)에 있는가"를 가리킨다 (`ref: refs/heads/main`).
- 커밋하면 **HEAD가 가리키는 브랜치 포인터만** 앞으로 이동한다.
- merge는 두 종류: fast-forward(포인터만 이동, 새 커밋 없음), 3-way(부모 2개인 merge commit 생성).

## 동작 원리
- `git switch -c`는 포인터 파일 하나를 만들 뿐이라 객체 수가 늘지 않는다.
- `git switch`는 HEAD뿐 아니라 작업 디렉터리와 index도 해당 커밋 상태로 바꾼다.
- 3-way merge는 공통 조상(merge-base)과 양쪽 끝 세 지점을 비교한다. 한쪽만 바꾼 부분은 자동 채택, 같은 곳을 다르게 바꾸면 conflict.
- conflict 중 index에는 같은 경로가 stage 1(base) / 2(ours) / 3(theirs)로 나뉘어 저장된다.
- merge 진행 상태는 `.git/MERGE_HEAD`에 기록되고, 진행 중에는 `switch`가 막힌다.
- 충돌 마커를 지운 뒤 `git add` → `git commit`까지 해야 merge가 끝난다. 포기는 `git merge --abort`.

## 실습에서 한 것
- 브랜치 생성 전후의 `.git/HEAD`, `refs/heads/*` 변화와 객체 개수 관찰.
- FF merge와 3-way merge를 각각 만들고 `git cat-file -p HEAD`로 parent 개수 확인.
- 같은 줄을 양쪽에서 수정해 conflict를 만들고, `ls-files --stage`로 stage 1/2/3을 확인한 뒤 해결.

## Infrastructure 연결
- 브랜치 이름이 곧 배포 정책이 된다 (feature/* → 테스트, main → staging, tag → prod).
- `values.yaml` 같은 설정 파일에서 conflict가 잦다. base/ours/theirs를 구분하면 판단이 쉽다.

## 면접 포인트
- branch는 포인터라 생성 비용이 0이고, HEAD는 현재 위치를 가리킨다.
- 3-way merge가 항상 충돌하는 건 아니다. 같은 부분을 다르게 바꿨을 때만 충돌한다.

## 내 말로 3줄 요약
1.Branch는 특정 커밋을 가리키는 포인터이며, HEAD는 현재 작업 중인 브랜치를 가리킨다. 따라서 브랜치 생성에는 별도의 객체 복사가 필요하지 않다.
2. Fast-forward는 브랜치 포인터만 이동하지만, 3-way merge는 공통 조상과 양쪽 커밋을 비교하여 두 부모를 가진 새로운 Merge Commit을 생성한다.
3. 같은 부분을 서로 다르게 수정하면 Conflict가 발생하며, Stage 1/2/3으로 각 버전을 구분한다. 직접 수정한 뒤 git add와 git commit으로 해결하고, 취소할 때는 git merge --abort를 사용한다.
