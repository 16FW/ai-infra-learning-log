#!/usr/bin/env bash
# Lesson 1: Git 내부 모델 (working dir / index / objects)
set -euo pipefail
WORK=$(mktemp -d) && cd "$WORK"
git init -q -b main

echo 'print("Hello, Git!")' > hello.py
git add hello.py
echo "objects after add:    $(find .git/objects -type f | wc -l)"   # blob 1개
git commit -q -m "feat: add hello.py"
echo "objects after commit: $(find .git/objects -type f | wc -l)"   # blob+tree+commit

echo 'print("Second line added")' >> hello.py
echo "--- git diff (working dir vs index)";  git diff
git add hello.py
echo "--- git diff --staged (index vs HEAD)"; git diff --staged
git commit -q -m "feat: add second line"

echo "--- commit -> tree -> blob"
git cat-file -p HEAD
git cat-file -p 'HEAD^{tree}'
git ls-files --stage
