## 2026-11-28 19:01:17
NAME                  READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES              SELECTOR
deployment.apps/web   3/3     3            3           67s   web          nginx:1.27-alpine   app=web

NAME                             DESIRED   CURRENT   READY   AGE   CONTAINERS   IMAGES              SELECTOR
replicaset.apps/web-5dcf5c46bf   3         3         3       46s   web          nginx:1.27-alpine   app=web,pod-template-hash=5dcf5c46bf

NAME                       READY   STATUS    RESTARTS   AGE   IP           NODE             NOMINATED NODE   READINESS GATES
pod/web-5dcf5c46bf-4gcq6   1/1     Running   0          34s   10.244.1.7   k8s-lab-worker   <none>           <none>
pod/web-5dcf5c46bf-qrdtg   1/1     Running   0          46s   10.244.1.4   k8s-lab-worker   <none>           <none>
pod/web-5dcf5c46bf-sw4xg   1/1     Running   0          46s   10.244.1.6   k8s-lab-worker   <none>           <none>

## [추가] 단독 Pod 삭제 (Q1)
k delete pod web-pod
pod "web-pod" deleted from lesson-02 namespace
k get pods
No resources found in lesson-02 namespace.
-> 단독 Pod는 다시 만들어지지 않음 (예측 일치)

## [추가] Deployment의 Pod 삭제 직후 (Q1)
k delete pod/web-5dcf5c46bf-5mvfr --wait=false
k get pods
NAME                   READY   STATUS              RESTARTS   AGE
web-5dcf5c46bf-4gcq6   0/1     ContainerCreating   0          1s
web-5dcf5c46bf-5mvfr   1/1     Terminating         0          13s
web-5dcf5c46bf-qrdtg   1/1     Running             0          13s
web-5dcf5c46bf-sw4xg   1/1     Running             0          13s
-> 지운 Pod가 Terminating인 동안 새 Pod(4gcq6)가 즉시 생성됨. 이름과 IP(10.244.1.7)가 새로 붙음 (예측 일치)
