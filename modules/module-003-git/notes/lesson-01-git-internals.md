# Lesson 01. Git의 내부 모델

## 핵심 개념
- Git은 diff를 쌓는 도구가 아니라 **각 커밋 시점의 스냅샷**을 저장한다.
- 세 영역: Working Directory → Staging Area(`.git/index`) → Repository(`.git/objects`)
- 세 객체: blob(파일 내용), tree(디렉터리 목록: 모드·타입·해시·이름), commit(tree + parent + 작성자 + 메시지)
- 모든 객체의 이름은 **내용의 해시**. 같은 내용이면 같은 해시 (파일명은 blob이 아니라 tree에 있다).

## 동작 원리
- `git init`이 바꾸는 것은 `.git` 디렉터리 하나. 이게 저장소의 정체.
- `git add`는 이미 blob을 `.git/objects`에 쓰고 index를 갱신한다 (객체 0 → 1).
- `git commit`은 작업 디렉터리가 아니라 **index를 읽어** tree와 commit을 만든다 (1 → 3).
- `git diff` = 작업 디렉터리 vs index, `git diff --staged` = index vs HEAD.
- commit 해시는 commit 객체 전체(tree, parent, author, 시각, 메시지)의 해시. 시각만 달라도 해시가 달라진다.

## 실습에서 한 것
- init → add → commit → diff 흐름을 예측 후 실행.
- `cat-file`로 commit → tree → blob을 직접 따라가며 구조 확인.
- 다른 저장소에서 같은 내용의 파일을 커밋해 blob 해시가 동일함을 확인.
- add/commit 전후 객체 개수를 세어 각 명령이 만드는 객체를 확인.

## Infrastructure 연결
- 내용 기반 해시 + 불변 객체 → Docker 이미지 레이어 digest, DVC의 데이터 변경 감지와 같은 원리.
- Dockerfile, K8s YAML, Terraform을 커밋으로 기록 → 배포·롤백·감사의 기준점(GitOps의 토대).

## 면접 포인트
- Staging Area는 "다음 커밋의 청사진"이고 실제 파일(`.git/index`)이다.
- Git은 스냅샷 저장소이며, 바뀌지 않은 파일은 기존 blob을 재사용한다.

## 내 말로 3줄 요약
1. Git은 변경 내역을 단순히 쌓는 것이 아니라, 각 커밋 시점의 스냅샷을 저장하며 blob, tree, commit 객체로 구성된다.
2. git add는 파일 내용을 blob으로 저장하고 index를 갱신하며, git commit은 index를 바탕으로 tree와 commit 객체를 생성한다.
3. 객체는 내용 기반 해시로 식별되므로 동일한 파일 내용은 같은 blob을 재사용할 수 있고, 커밋 시각 등 메타데이터가 달라지면 commit 해시도 달라진다.
