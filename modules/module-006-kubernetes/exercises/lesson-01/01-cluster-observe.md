## docker ps (k8s-lab)
NAMES                   IMAGE                  STATUS
k8s-lab-worker          kindest/node:v1.37.0   Up About a minute
k8s-lab-control-plane   kindest/node:v1.37.0   Up About a minute
## contexts
CURRENT   NAME           CLUSTER        AUTHINFO       NAMESPACE
          default        default        default        
*         kind-k8s-lab   kind-k8s-lab   kind-k8s-lab   
## nodes
NAME                    STATUS   ROLES           AGE   VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE                       KERNEL-VERSION                             CONTAINER-RUNTIME
k8s-lab-control-plane   Ready    control-plane   46s   v1.37.0   172.20.0.3    <none>        Debian GNU/Linux 13 (trixie)   6.6.87.2-microsoft-standard-WSL2 (amd64)   containerd://2.3.4
k8s-lab-worker          Ready    <none>          34s   v1.37.0   172.20.0.2    <none>        Debian GNU/Linux 13 (trixie)   6.6.87.2-microsoft-standard-WSL2 (amd64)   containerd://2.3.4
## pods -A
NAMESPACE            NAME                                            READY   STATUS    RESTARTS   AGE   IP           NODE                    NOMINATED NODE   READINESS GATES
kube-system          coredns-559f6c778d-26g9t                        1/1     Running   0          38s   10.244.0.4   k8s-lab-control-plane   <none>           <none>
kube-system          coredns-559f6c778d-pww4v                        1/1     Running   0          38s   10.244.0.2   k8s-lab-control-plane   <none>           <none>
kube-system          etcd-k8s-lab-control-plane                      1/1     Running   0          46s   172.20.0.3   k8s-lab-control-plane   <none>           <none>
kube-system          kindnet-6wgfm                                   1/1     Running   0          38s   172.20.0.3   k8s-lab-control-plane   <none>           <none>
kube-system          kindnet-9czsr                                   1/1     Running   0          34s   172.20.0.2   k8s-lab-worker          <none>           <none>
kube-system          kube-apiserver-k8s-lab-control-plane            1/1     Running   0          45s   172.20.0.3   k8s-lab-control-plane   <none>           <none>
kube-system          kube-controller-manager-k8s-lab-control-plane   1/1     Running   0          46s   172.20.0.3   k8s-lab-control-plane   <none>           <none>
kube-system          kube-proxy-6hqxg                                1/1     Running   0          34s   172.20.0.2   k8s-lab-worker          <none>           <none>
kube-system          kube-proxy-c5zwd                                1/1     Running   0          38s   172.20.0.3   k8s-lab-control-plane   <none>           <none>
kube-system          kube-scheduler-k8s-lab-control-plane            1/1     Running   0          46s   172.20.0.3   k8s-lab-control-plane   <none>           <none>
local-path-storage   local-path-provisioner-75f7fc7dc5-qvqpl         1/1     Running   0          38s   10.244.0.3   k8s-lab-control-plane   <none>           <none>
## server version
Client Version: v1.34.1
Kustomize Version: v5.7.1
Server Version: v1.37.0
Warning: version difference between client (1.34) and server (1.37) exceeds the supported minor version skew of +/-1

## [A-3] 2026-11-27 21:37:45 / other-project 중지 / kind k8s-lab 구동 중
KUBECONFIG=[/home/eunho/.kube/config]
## server (kind-k8s-lab)
https://127.0.0.1:40411
## docker port (k8s-lab)
6443/tcp -> 127.0.0.1:40411
## df -h /mnt/c
Filesystem      Size  Used Avail Use% Mounted on
C:\             220G  220G  557M 100% /mnt/c
## docker system df
TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          22        3         6.046GB   2.846GB (47%)
Containers      4         2         4.755MB   581.6kB (12%)
Local Volumes   11        7         6.564GB   258.9MB (3%)
Build Cache     69        0         1.582GB   1.251GB
## kind version
kind v0.33.0 go1.26.7 linux/amd64
