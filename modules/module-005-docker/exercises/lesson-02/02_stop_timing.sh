#!/usr/bin/env bash
cd "$(dirname "$0")"

run_case() {
  name=$1; mode=$2; shift 2
  docker rm -f "$name" >/dev/null 2>&1
  docker run -d --name "$name" "$@" -e MODE="$mode" \
    -v "$PWD":/work python:3.12-slim python /work/sigtest.py >/dev/null
  sleep 2
  t0=$(date +%s.%N)
  docker stop "$name" >/dev/null
  t1=$(date +%s.%N)
  elapsed=$(awk "BEGIN{printf \"%.1f\", $t1-$t0}")
  code=$(docker inspect -f '{{.State.ExitCode}}' "$name")
  echo "$name: stop ${elapsed}s, exit=$code"
  docker rm "$name" >/dev/null
}

run_case case_A A
run_case case_B B
run_case case_A_init A --init
