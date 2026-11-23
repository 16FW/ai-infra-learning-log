# Lesson 06. GPU Basics: CPU vs GPU, VRAM, 측정의 함정

## 핵심 개념
- GPU는 수천 개의 단순한 코어와 전용 메모리(VRAM)를 가진 병렬 프로세서다. 행렬곱처럼 같은 연산을 많은 원소에 반복하는 작업에 유리하다. 데이터는 RAM → PCIe → VRAM → 연산 → 다시 RAM 경로로 오간다.
- 세 가지 함정: 전송 비용(연산이 작으면 이득이 깎인다), 비동기 실행(시간을 재려면 `torch.cuda.synchronize()` 필요), 워밍업(첫 호출의 CUDA 초기화 등 일회성 비용).
- GPU 메모리는 세 값을 구분한다: `memory_allocated`(텐서가 실제 쓰는 양), `memory_reserved`(캐시 할당기가 확보한 양), `nvidia-smi`(reserved + CUDA 컨텍스트 + 다른 프로세스).
- `nvidia-smi` 오른쪽 위의 "CUDA Version"은 설치된 CUDA가 아니라 드라이버가 지원하는 최대 CUDA 버전이고, torch가 쓰는 런타임(`torch.version.cuda`)과 별개다.
- batch를 키우면 처리량이 늘다가 포화되고 그 뒤로는 지연만 늘어난다. fp16은 속도와 메모리를 개선하지만 정밀도를 포기한다.

## 동작 원리
- `Tensor.to(dev)`는 새 텐서를 반환하고 원본은 그대로다. `Module.to(dev)`는 모델을 제자리에서 바꾸고 자기 자신을 반환한다.
- 서로 다른 장치의 텐서를 연산하면 `RuntimeError: Expected all tensors to be on the same device`가 난다.
- 비동기 실행이라 `synchronize` 없이 재면 "일을 던지는 시간"만 잰다. 결과를 이론 성능과 비교해 타당성을 확인한다(15~19µs는 약 8 PFLOPS에 해당해 T4 이론 피크(약 8 TFLOPS)의 약 1000배라 불가능).
- 캐시 할당기는 `del` 후에도 메모리를 reserved로 들고 있어서 `nvidia-smi` 사용량이 안 줄고, `empty_cache()` 후에 돌아온다.
- OOM은 `torch.cuda.OutOfMemoryError`로 잡을 수 있고, 잡으면 프로세스는 죽지 않는다.
- GPU 선택 로직은 `torch.cuda.is_available`만 monkeypatch하면 GPU 없이 테스트할 수 있다. `torch.device("cuda")` 객체는 GPU 없이도 만들 수 있다. 텐서를 올릴 때 CPU 전용 빌드는 `Torch not compiled with CUDA enabled`가 난다.

## 실습에서 한 것
환경: Colab Tesla T4(compute capability 7.5, total 14.56GiB), torch 2.14.1+cu130, 드라이버 580.82.07. CPU 비교는 torch 1스레드 기준.
- 행렬곱(fp32): 4096에서 CPU 1276.99ms(약 108 GFLOPS) vs GPU 33.19ms(약 4.1 TFLOPS) = 38.5배. 512는 17.9배였고, 입력 2개의 H2D 복사를 포함하면 2.7배(결과 D2H는 제외). `synchronize` 없이 재면 15~19µs.
- ResNet50 추론(p50 ms / img/s / 피크 MiB):
  - CPU fp32: batch 1 122.35 / 8.2, batch 8 1177.56 / 6.8, batch 32 5368.29 / 6.0
  - GPU fp32: batch 1 8.41 / 118.9 / 133.8, batch 8 24.40 / 327.9 / 190.1, batch 32 84.49 / 378.7 / 442.8
  - GPU fp16: batch 1 9.73 / 102.8 / 64.0, batch 8 11.01 / 726.8 / 103.8, batch 32 38.95 / 821.5 / 241.1
  - batch 8 → 32에서 처리량은 13~15%만 늘고 지연은 약 3.5배라 연산이 batch 8~16 근처에서 포화됐다. fp16은 batch 32에서 속도 2.17배, 피크 메모리 0.54배(batch 1은 오히려 약간 느렸고, 이유는 가설이며 반복 측정이 필요).
- 메모리 단계(allocated / reserved / smi, MiB): 시작 0 / 0 / 225, 1GiB씩 3번 할당하면 3072 / 3072 / 3297, 삭제 후 0 / 3072 / 3297, empty_cache 후 0 / 0 / 225. smi − reserved = 225MiB (우리 프로세스 CUDA 컨텍스트 약 102MiB + 다른 프로세스 PID 1307 약 120MiB, 정체 미확인).
- ResNet50 이미지당 활성 메모리 증가량(fp32): batch 1→32 구간 약 10.0MiB/이미지((442.8−133.8)/31), 32→128 구간 약 10.5MiB/이미지((1453.9−442.8)/96)로 거의 선형이다. 같은 batch 1 fp32 피크가 두 스크립트에서 133.8MiB와 125.6MiB로 달랐던 이유: 첫 호출만 재면 125.6MiB, 여러 번 호출한 뒤에는 133.8MiB였다(같은 프로세스에서 1회 125.6 / 23회 133.8 / 이후 다시 1회 133.8). 호출을 몇 번 한 뒤의 정상 상태 피크가 첫 호출보다 약 8.2MiB 높았고, 이 8.2MiB의 정체는 확인하지 못했다. 그래서 메모리 예산은 첫 호출이 아니라 워밍업 후 정상 상태 피크로 잡는다.
- 7B fp16: 가중치 13.04GiB, T4 total 14.56GiB, 여유 1.52GiB, 토큰당 KV cache 512KiB → 배치 1에서 약 3119토큰(CUDA 컨텍스트와 중간값을 빼면 약 2900). 가중치는 들어가지만 실서비스는 어렵다.
- `device_select.py`: `cuda` 요청인데 GPU가 없으면 RuntimeError로 실패한다(폴백은 `auto`로 따로 표현). 조용히 CPU로 가면 batch에 따라 약 15~63배 느려지는데 배포 직후 알아채기 어렵기 때문이다. pytest 6개 통과.
- 한계: fp16 정확도는 확인하지 않았고, p95와 대기 시간은 재지 않았고, 배치 크기는 1/8/32만 재서 포화 지점은 8~16 사이로만 추정했다.

## Infrastructure 연결
- 컨테이너에서 GPU를 쓰려면 호스트에 NVIDIA 드라이버와 컨테이너 툴킷을, 이미지에 CUDA 런타임과 프레임워크를 둔다(Module 005, 006에서 실습).
- 모델 서빙의 메모리 예산은 가중치 + KV cache + 여유로 계산해서 GPU 종류와 동시 요청 수를 정한다.
- GPU 서버는 `cuda` 요청 시 폴백하지 않고 실패(readiness 실패)시키는 편이 안전하다. 선택 로직은 GPU 없는 CI에서 monkeypatch로 테스트한다.
- 벤치마크에는 GPU 이름, 드라이버/CUDA 버전, CPU 스레드 수를 같이 기록한다(Colab은 배정 GPU가 달라질 수 있다).
- GPU는 놀리면 비용이 나가므로 사용률 모니터링과 배칭이 핵심이다.

## 면접 포인트
- GPU 벤치마크에서 워밍업과 `synchronize`가 필요한 이유, 결과를 이론 성능과 비교해 타당성을 검사하는 법.
- CUDA OOM: allocated 증가(누수) vs reserved만 큼(캐시/단편화), 피크는 가장 긴 요청 × 동시 요청 수, 입력 검증과 배치/동시성 제한으로 대응.

## 내 말로 3줄 요약
1. GPU는 수천 개의 단순 코어와 전용 메모리로 행렬곱을 병렬 처리해서 이번 측정에서 4096 행렬곱이 CPU(1스레드)보다 38.5배, ResNet50 batch 32는 63배(fp16은 137배) 빨랐지만, 연산이 작으면 CPU→GPU 복사 비용이 이득을 깎는다(512는 17.9배 → 2.7배).
2. GPU 측정은 비동기라서 워밍업과 synchronize가 필수이고 빼면 실제의 약 1950배 작은 값이 나오며(이론 성능과 비교해 타당성을 검사한다), batch를 키우면 처리량은 포화되고 지연만 늘며(batch 8→32에서 +13~15%, 지연 3.5배), fp16은 속도와 메모리를 개선하는 대신 정밀도를 포기한다.
3. GPU 메모리는 allocated, reserved, nvidia-smi 세 값을 구분해야 하고(del 후에도 reserved 유지, empty_cache 후 반환), 7B fp16(13.04GiB)은 T4(14.56GiB)에 가중치만 겨우 들어가 KV cache 여유가 1.52GiB(배치 1에서 약 3천 토큰)뿐이라, 서빙 설계는 가중치 + KV cache + 여유로 GPU 종류와 동시 요청 수를 정한다.
