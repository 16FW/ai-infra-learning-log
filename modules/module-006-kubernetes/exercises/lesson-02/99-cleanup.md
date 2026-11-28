## 정리 (2026-11-28 19:0x)
k get all (삭제 전): Pod 3개(web-59d784f4ff-*), Deployment web 3/3, ReplicaSet 2개
kubectl --context kind-k8s-lab delete namespace lesson-02
-> namespace "lesson-02" deleted
get ns(삭제 후): default, kube-node-lease, kube-public, kube-system, local-path-storage
kind 클러스터 k8s-lab은 유지
