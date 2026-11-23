#!/usr/bin/env bash
sudo unshare --pid --fork --mount-proc --uts bash -c '
echo "내 PID: $$"
ps aux
echo "변경 전 hostname: $(hostname)"
hostname container-test
echo "변경 후 hostname(namespace 안): $(hostname)"
sleep 20
'
