#!/usr/bin/env bash
# Lesson 2: branch = pointer, fast-forward, 3-way merge, conflict
set -euo pipefail
WORK=$(mktemp -d) && cd "$WORK"
git init -q -b main
echo 'print("base")' > app.py
git add app.py && git commit -q -m "chore: base"

echo "== branch is a pointer"
git switch -q -c feature
cat .git/HEAD; cat .git/refs/heads/feature
echo 'print("feature")' >> app.py
git commit -qam "feat: feature change"
git switch -q main
git merge feature                       # fast-forward

echo "== 3-way merge"
git switch -q -c feature-a
echo 'a' > a.py && git add a.py && git commit -q -m "feat: add a.py"
git switch -q main
echo 'b' > b.py && git add b.py && git commit -q -m "feat: add b.py"
git merge feature-a -m "merge: feature-a"
git cat-file -p HEAD                    # parent 2개

echo "== conflict (stage 1/2/3)"
BASE=$(git rev-parse HEAD)
echo 'print("main version")' > app.py && git commit -qam "fix: main version"
git switch -q -c conflict-test "$BASE"
echo 'print("feature version")' > app.py && git commit -qam "fix: feature version"
git switch -q main
git merge conflict-test || true
git ls-files --stage app.py
cat app.py
git merge --abort
