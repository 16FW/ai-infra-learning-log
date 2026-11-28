
## [A-1] 측정 조건: 2026-11-27 21:22:20 / WSL2 + Docker Desktop / other-project 구동 중
## nproc
4
## free -h
               total        used        free      shared  buff/cache   available
Mem:           7.4Gi       914Mi       3.5Gi       4.7Mi       3.3Gi       6.5Gi
Swap:          4.0Gi          0B       4.0Gi
## df -h ~
Filesystem      Size  Used Avail Use% Mounted on
/dev/sdd       1007G   24G  933G   3% /
## docker ps -a
NAMES                     IMAGE                            STATUS
k3d-other-project-serverlb   ghcr.io/k3d-io/k3d-proxy:5.8.3   Exited (137) 2 minutes ago
k3d-other-project-server-0   rancher/k3s:v1.31.5-k3s1         Exited (137) 2 minutes ago
## docker network ls
NETWORK ID     NAME                 DRIVER    SCOPE
e6700c099bc9   bridge               bridge    local
3a47340a6310   host                 host      local
22678f9ee515   k3d-other-project       bridge    local
df5807c6e8e5   none                 null      local
d1f5c59cb24d   other-project_default   bridge    local
## kubectl
Client Version: v1.34.1
Kustomize Version: v5.7.1
## kind
kind v0.33.0 go1.26.7 linux/amd64
## helm
version.BuildInfo{Version:"v3.22.1", GitCommit:"d6c1a0e4027caa6abc7892e7ea9f0cda7447baa3", GitTreeState:"clean", GoVersion:"go1.26.9"}
## contexts
CURRENT   NAME      CLUSTER   AUTHINFO   NAMESPACE
*         default   default   default    
## current-context
default
## [정정] A-1 시점 other-project 컨테이너는 Exited(137) 상태(구동 중 아님). 메모리 baseline은 other-project 미구동 기준
