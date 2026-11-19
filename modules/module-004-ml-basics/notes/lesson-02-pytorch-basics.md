# Lesson 02. PyTorch Basics: tensor, state_dict, 추론 파이프라인

## 핵심 개념
- tensor는 shape, dtype, device를 가진 N차원 배열이다. dtype은 메모리 크기를, device는 연산 위치를, shape은 서빙 입력의 계약을 결정한다.
- nn.Module은 구조(코드)이고, state_dict는 학습된 값(파라미터 + 버퍼)이다. 버퍼는 학습되지 않지만 저장되는 상태다(예: BatchNorm의 이동 평균/분산).
- 저장 방식은 두 가지다. state_dict 저장은 값만 저장하고 구조 코드는 따로 필요하다. 전체 모델 저장은 클래스를 모듈 경로로 참조하므로 그 경로가 바뀌면 깨진다.
- model.eval()은 Dropout, BatchNorm 같은 층의 동작을 바꾸고, torch.no_grad()는 자동 미분 기록을 끈다. 추론에서는 둘 다 쓴다.
- 추론 파이프라인: 전처리 → batch 차원 추가 → eval + no_grad forward → softmax → top-k.

## 동작 원리
- torch.save 결과물은 압축 없는 zip이다. data.pkl(구조/키), data/N(텐서 원본 바이트, 정렬됨), 버전 정보가 들어 있다. 60바이트 파라미터가 1869바이트 파일이 되는 것은 항목 수에 비례하는 고정 오버헤드 때문이고, 큰 모델에서는 무시할 수준이다.
- 전체 모델 저장은 클래스를 `모듈.클래스` 이름으로 pickle에 기록한다. 스크립트를 직접 실행해 저장하면 `__main__.TinyNet`, 모듈에서 import해 저장하면 `tiny_net.TinyNet`이 된다. 로드 시 모듈이 없으면 ModuleNotFoundError, 모듈은 있는데 클래스가 없으면 AttributeError가 난다.
- torch.load의 기본값은 weights_only=True(PyTorch 2.6~)라서 허용 목록 밖의 클래스를 거부한다. weights_only=False는 임의 코드가 실행될 수 있어 신뢰할 수 있는 파일에만 쓴다.
- no_grad 없이 실행하면 역전파용 중간 결과(계산 그래프)를 메모리에 보관한다. 추론에서는 낭비이고 큰 모델에서는 OOM 위험이 된다.

## 실습에서 한 것
- tensor dtype/element_size/type promotion 예측 후 검증(fp16 + fp32 → fp32).
- TinyNet(Linear 4→3): 파라미터 15개, 60바이트, tiny.pt 1869바이트. 새 인스턴스에 load_state_dict로 복원 후 torch.equal로 확인.
- 저장 방식 3가지 로드 실험: 클래스 없는 폴더(ModuleNotFoundError), 기본 로딩(Unsupported global), weights_only=False(성공/AttributeError).
- ResNet50(IMAGENET1K_V2): 파라미터 25,557,032개 = 102,228,128바이트. 체크포인트는 +312,289바이트(버퍼 212,904 + 오버헤드). 로딩 전 RSS 약 676MiB(import torch만으로), 로딩 후 +118.67MiB(가중치 약 97.5MiB보다 큼).
- 전처리 후 (3,224,224) float32 → batch 차원 추가 (1,3,224,224). top-5 출력.
- 지연시간: 워밍업 제외, p50 290.67 ms / p95 454.57 ms (batch=1). 배치 32의 처리량은 3.13 img/s로, batch=1 대비 0.9배였다.
- classify_cli.py: 정상 0, 파일/이미지/인자 오류는 2. CLI는 실행마다 모델을 다시 로드한다(`time` 측정: 50.488초).

## Infrastructure 연결
- 서빙 이미지에는 구조 코드(버전 고정)와 state_dict가 함께 들어간다. 이를 하나로 묶는 것이 TorchServe의 .mar 아카이브다.
- 컨테이너 메모리 request는 프레임워크 기본 RSS + 가중치 + 로딩 오버헤드를 모두 더해서 정한다.
- 모델은 서버 시작 시 한 번 로드하고 요청마다 재사용해야 한다(CLI의 cold start 비용 → FastAPI 서빙 설계).
- SLO는 평균이 아니라 p95/p99로 정한다. 종료 코드는 CI/CD, Job, CronJob의 성공/실패 판단 기준이다.
- 외부 모델 파일은 공급망 공격의 통로가 될 수 있다. weights_only와 출처 검증이 필요하다.

## 면접 포인트
- state_dict + 버전 고정된 구조 코드로 배포하는 것이 기본이며, 전체 모델 pickle은 모듈 경로에 묶이고 weights_only=False는 임의 코드 실행 위험이 있다.
- eval()은 층의 동작을, no_grad()는 계산 기록(메모리)을 바꾼다. p95로 SLO를 정하는 이유는 평균이 느린 요청을 가리기 때문이다.

## 내 말로 3줄 요약
1. PyTorch 모델은 구조 코드(nn.Module)와 학습된 값(state_dict: 파라미터 + 버퍼)으로 나뉘며, 프로덕션에서는 state_dict와 버전 고정된 구조 코드를 함께 배포하는 것이 안전하다(전체 모델 pickle은 모듈 경로에 묶여 깨지기 쉽고 weights_only=False는 임의 코드 실행 위험이 있다).
2. 추론은 전처리로 입력 계약(shape, dtype, batch 차원)을 맞추고 eval()과 no_grad()로 실행하며, eval은 층의 동작을, no_grad는 계산 기록(메모리)을 바꾼다.
3. 모델의 실제 메모리는 가중치 크기보다 크고(ResNet50: 약 97.5MiB 가중치 → RSS +118.7MiB, import 후 기본 RSS 약 676MiB는 별도), 지연시간은 평균이 아니라 p95로 봐야 하므로, 리소스 request와 SLO는 직접 측정한 값으로 정해야 한다.
