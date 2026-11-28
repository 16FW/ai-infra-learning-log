## 롤링 업데이트: nginx:1.27-alpine -> nginx:1.27.4-alpine (2026-11-28 19:0x)
sed로 deployment.yaml의 image를 변경 후 k apply -f deployment.yaml
-> deployment.apps/web configured
직후 k get pods: 새 Pod 1개 ContainerCreating + 옛 Pod 3개 Running (총 4개)
  web-59d784f4ff-nztlw 0/1 ContainerCreating 1s
  web-5dcf5c46bf-4gcq6 / -qrdtg / -sw4xg 1/1 Running
k rollout status: 1 out of 3 -> 2 out of 3 -> 1 old replicas are pending termination -> successfully rolled out
k get rs
  web-59d784f4ff   3 3 3   22s
  web-5dcf5c46bf   0 0 0   5m33s   (옛 ReplicaSet은 0개로 남음)
k rollout history deployment/web
  REVISION 1, 2 (CHANGE-CAUSE는 둘 다 <none>)
예측: 옛 ReplicaSet은 0개로 남는다 / 직후 Pod는 4개 -> 둘 다 일치

## 측정 조건
2026-11-28 19:0x, tradeproof 중지, kind k8s-lab(노드 2개), lesson-02 네임스페이스
이전 태그 nginx:1.27-alpine(노드에 이미 있음) -> 새 태그 nginx:1.27.4-alpine(노드가 새로 받음)
이미지 태그는 Docker Hub에서 미리 확인하지 않고 선택, 롤아웃 성공과 crictl(20.8MB)로 존재 확인

## 관찰
- ReplicaSet 해시: 옛 5dcf5c46bf -> 새 59d784f4ff
- 새 Pod 이름: web-59d784f4ff-nztlw, -s2cgm, -t8llr
- apply 직후: 새 Pod 1개 ContainerCreating + 옛 Pod 3개 Running = 4개
- rollout status 흐름: 1 of 3 -> 2 of 3 -> 1 old replicas pending termination -> successfully rolled out
- 새 ReplicaSet 나이 22s(전체 교체에 약 20초대)

## 사실과 가설
사실: 한 번에 1개씩 교체됨, 옛 ReplicaSet은 0개로 남음, REVISION 1, 2
가설(미검증): 교체 중 READY가 항상 3 이상으로 유지됨 (중간 Pod 목록은 get pod -w로 기록하지 못함)
가설(미검증): maxSurge/maxUnavailable이 기본 25%

## 측정 조건
2026-11-28 19:0x, tradeproof 중지, kind k8s-lab(노드 2개), lesson-02 네임스페이스
이전 태그 nginx:1.27-alpine(노드에 이미 있음) -> 새 태그 nginx:1.27.4-alpine(노드가 새로 받음)
이미지 태그는 Docker Hub에서 미리 확인하지 않고 선택, 롤아웃 성공과 crictl(20.8MB)로 존재 확인

## 관찰
- ReplicaSet 해시: 옛 5dcf5c46bf -> 새 59d784f4ff
- 새 Pod 이름: web-59d784f4ff-nztlw, -s2cgm, -t8llr
- apply 직후: 새 Pod 1개 ContainerCreating + 옛 Pod 3개 Running = 4개
- rollout status 흐름: 1 of 3 -> 2 of 3 -> 1 old replicas pending termination -> successfully rolled out
- 새 ReplicaSet 나이 22s(전체 교체에 약 20초대)

## 사실과 가설
사실: 한 번에 1개씩 교체됨, 옛 ReplicaSet은 0개로 남음, REVISION 1, 2
가설(미검증): 교체 중 READY가 항상 3 이상으로 유지됨 (중간 Pod 목록은 get pod -w로 기록하지 못함)
가설(미검증): maxSurge/maxUnavailable이 기본 25%
