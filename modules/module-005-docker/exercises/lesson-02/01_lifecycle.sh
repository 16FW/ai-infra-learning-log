#!/usr/bin/env bash
N=lc1
docker rm -f $N >/dev/null 2>&1
show() { echo "[$1] $(docker inspect -f '{{.State.Status}} exit={{.State.ExitCode}}' $N)"; }

docker create --name $N alpine sleep 300 >/dev/null; show "create"
docker start $N >/dev/null;                          show "start"
time docker stop $N >/dev/null;                      show "stop"
docker start $N >/dev/null;                          show "재start"
docker kill $N >/dev/null;                           show "kill"
docker rm $N >/dev/null
