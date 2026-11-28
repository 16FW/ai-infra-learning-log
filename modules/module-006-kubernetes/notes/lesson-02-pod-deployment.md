# Lesson 2. Pod와 Deployment

## 핵심 개념
- Pod: 컨테이너를 감싸는 최소 배포 단위. 한 Pod 안의 컨테이너는 네트워크와 저장소를 공유한다.
- ReplicaSet: 특정 Pod가 N개 있어야 한다는 것을 지키는 객체. 부족하면 만들고 넘치면 지운다.
- Deployment: ReplicaSet을 관리해 버전 교체(롤링 업데이트)와 롤백을 맡는다.
- 라벨(label)과 셀렉터(selector): selector는 "내 Pod의 기준", template.labels는 만들어지는 Pod의 이름표. 둘이 맞아야 한다.
- 네임스페이스(namespace): 이름 칸막이. 실습을 한 칸에 가두면 정리가 한 줄이다.

## 동작 원리
- 단독 Pod를 지우면 다시 만들어 주는 주체가 없어 사라진다.
- Deployment의 Pod를 지우면 ReplicaSet 컨트롤러가 현재 개수 ≠ 원하는 개수를 발견해 새 Pod를 만든다(이름과 IP가 새로 붙음).
- 롤링 업데이트: 새 ReplicaSet을 만들고 새 것은 늘리고 옛 것은 줄인다. maxSurge(임시로 더 띄울 수)와 maxUnavailable(내려도 되는 수)이 한 번에 움직이는 폭을 제한한다. 3개일 때 surge는 올림 1, unavailable은 내림 0.
- 옛 ReplicaSet은 0개로 남아 이전 버전의 설계도를 보관하므로 롤백은 새로 빌드할 필요 없이 개수만 되돌리면 된다.
- 이미지 저장소는 노드(containerd)마다 따로다. 첫 Pod는 이미지를 받았고, 같은 노드의 두 번째 Pod는 캐시를 썼다.

## 실습에서 한 것
- nginx:1.27-alpine 단독 Pod, replicas 3 Deployment 작성과 적용.
- Pod 삭제 후 복구 관찰: 새 Pod는 이름과 IP가 달라짐. 삭제된 Pod가 Terminating인 동안 대체 Pod가 이미 생성됨.
- 이미지 태그를 1.27.4-alpine으로 바꿔 롤링 업데이트: ReplicaSet 5dcf5c46bf → 59d784f4ff, 한 번에 하나씩 교체, 옛 ReplicaSet은 0개로 남음, REVISION 1 → 2.

## Infrastructure 연결
- 모델 서빙 서버를 복제본으로 띄우고, 새 모델 버전은 롤링으로 교체하며, 문제가 있으면 옛 ReplicaSet으로 롤백하는 기반이다.
- 컨트롤 플레인이 멈춰도 이미 실행 중인 Pod는 계속 동작하지만, 새 Pod 생성과 복구는 멈춘다.

## 면접 포인트
- Deployment가 단독 Pod 대신 필요한 이유: 단독 Pod는 죽으면 다시 만들어 줄 주체가 없다. Deployment는 ReplicaSet이 원하는 개수와 현재 개수의 차이를 계속 비교해 부족하면 새 Pod를 만들기 때문에 자가 치유가 된다.
- selector와 template.labels가 같아야 하는 이유: ReplicaSet은 selector로 자기 Pod를 찾아 개수를 센다. 만들어진 Pod에 같은 라벨이 없으면 자기 것으로 인식하지 못해 개수를 맞출 수 없으므로 API Server가 apply 단계에서 거부한다.
- 롤링 업데이트의 교체 원리: 새 ReplicaSet을 만들어 늘리고 옛 것을 줄이되, maxSurge(임시로 더 띄울 수 있는 수)와 maxUnavailable(내려도 되는 수)로 한 번에 움직이는 폭을 제한한다. 3개일 때 surge는 올림 1, unavailable은 내림 0이라 새 Pod 1개가 Ready가 된 뒤 옛 Pod 1개를 내린다.
- 롤백이 빠른 이유: 옛 ReplicaSet이 0개로 남아 이전 버전의 설계도를 보관하므로, 새로 빌드하지 않고 개수만 되돌리면 된다.
- 컨트롤 플레인이 멈췄을 때: 실행 중인 Pod는 노드의 kubelet이 계속 돌려서 서비스는 유지되지만, 새 Pod 생성과 복구는 멈춘다.

## 내 말로 3줄 요약
1. Deployment는 ReplicaSet을 통해 Pod 개수를 유지하고, Pod를 지워도 개수 차이를 보고 새 Pod를 만든다. 단독 Pod는 되살아나지 않는다.
2. 롤링 업데이트는 새 ReplicaSet을 늘리고 옛 것을 줄이는 방식이며, maxSurge와 maxUnavailable이 속도를 제한하고 옛 ReplicaSet이 롤백 근거로 남는다.
3. 컨트롤 플레인이 느려지면 실행 중인 Pod는 유지되지만 새 Pod 생성 같은 조정 작업은 지연된다.
