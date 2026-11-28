## 2026-11-28 18:59:08 (namespace lesson-02)
## get pods -o wide
NAME      READY   STATUS    RESTARTS   AGE   IP           NODE             NOMINATED NODE   READINESS GATES
web-pod   1/1     Running   0          81s   10.244.1.3   k8s-lab-worker   <none>           <none>
## describe (Events)
Events:
  Type    Reason     Age   From               Message
  ----    ------     ----  ----               -------
  Normal  Scheduled  81s   default-scheduler  Successfully assigned lesson-02/web-pod to k8s-lab-worker
  Normal  Pulled     80s   kubelet            spec.containers{web}: Container image "nginx:1.27-alpine" already present on machine and can be accessed by the pod
  Normal  Created    80s   kubelet            spec.containers{web}: Container created
  Normal  Started    80s   kubelet            spec.containers{web}: Container started
## logs (끝 5줄)
2026/11/28 09:57:51 [notice] 1#1: start worker processes
2026/11/28 09:57:51 [notice] 1#1: start worker process 33
2026/11/28 09:57:51 [notice] 1#1: start worker process 34
2026/11/28 09:57:51 [notice] 1#1: start worker process 35
2026/11/28 09:57:51 [notice] 1#1: start worker process 36
