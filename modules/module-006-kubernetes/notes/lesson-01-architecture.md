# Lesson 1. 쿠버네티스 아키텍처

## 핵심 개념
- 클러스터 = 노드 여러 대를 한 덩어리로 묶은 것. 노드는 컨트롤 플레인(결정)과 워커(실행)로 나뉜다.
- 컨트롤 플레인: API Server(유일한 입구), etcd(상태 저장), Scheduler(배치), Controller Manager(조정).
- 워커: kubelet(노드 담당자), 컨테이너 런타임(containerd), kube-proxy(네트워크 규칙).
- 원하는 상태(desired state)를 선언하면 컨트롤러가 현재 상태와 비교해 차이를 없애는 조정 루프(reconciliation loop)가 돈다.

## 동작 원리
- kubectl apply → API Server가 인증·검증 후 etcd에 저장.
- Deployment 컨트롤러가 ReplicaSet을, ReplicaSet 컨트롤러가 Pod 객체를 만든다.
- Scheduler가 노드 미정 Pod에 노드를 기록하고, 해당 노드의 kubelet이 런타임에 컨테이너 실행을 시킨다.
- 모든 구성 요소는 API Server를 통해서만 읽고 쓴다(etcd와 직접 통신하는 건 API Server뿐).

## 실습에서 한 것
- kind 클러스터(control-plane 1 + worker 1) 관찰. 노드 = Docker 컨테이너 2개로 보임(예측 일치).
- kube-system에 컨트롤 플레인 부품 4개가 Pod로 보임(예측 일치).
- 관찰한 사실: 컨트롤 플레인 노드의 /etc/kubernetes/manifests에 부품 4개의 YAML이 있음.
- kubelet이 이 폴더를 읽어 직접 띄우는 방식(static Pod).

## Infrastructure 연결
- Docker 데몬이 한 서버에서 하던 일을 kubelet+런타임이 노드마다 하고, 여러 서버에 걸친 "있어야 한다"는 컨트롤 플레인이 유지한다.
- 모델 서빙 복제본의 자동 복구, 롤링 배포, 스케일링의 기반이 이 조정 루프다.

## 면접 포인트
- 쿠버네티스가 "선언적"이라는 의미와 조정 루프를 설명할 수 있어야 한다.
- apply 한 번이 거치는 구성 요소 경로를 순서대로 말할 수 있어야 한다.

## 내 말로 3줄 요약
1. 쿠버네티스는 "무엇이 몇 개 있어야 한다"를 선언하면, 컨트롤러가 현재 상태와 비교해 차이를 계속 메우는 시스템이다.
2. 요청은 모두 API Server를 거쳐 etcd에 저장되고, Controller Manager·Scheduler·kubelet이 각자 API Server를 보다가 자기 일을 한다.
3. 컨트롤 플레인 부품도 kube-system에 Pod로 보이며, 자원이 모자라면 컨트롤 플레인이 재시작될 수 있다(원인은 미검증).
