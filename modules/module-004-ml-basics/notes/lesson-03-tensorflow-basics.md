# Lesson 03. TensorFlow Basics: Keras 3 저장 형식, SavedModel, 추론 비교

## 1. 핵심 개념
- `model.save()`는 `.keras` 모델 저장, `model.export()`는 서빙용 SavedModel 생성에 사용한다.
- `.keras`는 편집·재학습에 적합하고, SavedModel은 계산 그래프·가중치·시그니처를 포함해 모델 코드 없이 추론할 수 있다.
- Keras 3에서 SavedModel은 `keras.models.load_model()`로 직접 로드할 수 없으며, `tf.saved_model.load()`를 사용한다.
- 모델마다 입력 레이아웃과 전처리 방식이 다르다. MobileNetV2는 NHWC 및 [-1, 1] 정규화, PyTorch ResNet50은 NCHW 및 mean/std 정규화를 사용한다.
- `tf.function`은 첫 호출 때 그래프를 생성하므로 초기 호출이 느리며, 이후 그래프 실행은 빨라진다.

## 2. 동작 원리
- `.keras`는 모델 설정(config), 버전 정보(metadata), 가중치(weights)를 포함하는 ZIP 아카이브다.
- SavedModel은 `saved_model.pb`, `variables/`, `fingerprint.pb` 등으로 구성된다.
- SavedModel의 시그니처는 입력·출력 이름, shape, dtype을 정의하며 서빙 API의 계약 역할을 한다.
- 이번 실습의 SavedModel은 `serve`, `serving_default` 시그니처를 제공하고 입력은 `keras_tensor`, 출력은 `output_0`으로 확인됐다.

## 3. 실습 결과

### TinyNet 저장 및 로드
- Dense(4→3) 모델의 파라미터는 15개, FP32 기준 60 bytes였다.
- `.keras` 파일 크기: 11,583 bytes
- SavedModel 크기: 23,083 bytes
- `.keras`와 `tf.saved_model.load()`를 통한 로드 및 추론에 성공했다.
- `load_model()`로 SavedModel을 로드하면 Keras 3에서 ValueError가 발생한다.

### MobileNetV2
- 파라미터: 3,538,984개
- FP32 가중치 크기: 14,155,936 bytes (약 13.50 MiB)
- 로드 후 RSS: 594.38 MiB (import 후 약 536 MiB)
- RSS 증가량: 58.84 MiB (가중치 크기의 약 4.4배)
- 로드 시간: 8.66초 (다운로드 포함 여부는 기존 측정 로그로 확인 불가)
- 입력: `(1, 224, 224, 3)`, float32
- 전처리: 값 범위 [-1, 1]

### 추론 성능 (CPU)
| 호출 방식 | Batch 1 p50 |
|---|---:|
| `model.predict()` | 145.45 ms |
| 직접 호출 | 240.47 ms |
| `tf.function` | 43.93 ms |
| `tf.function` 첫 호출 | 1,221.04 ms |

| Batch | 처리량 |
|---|---:|
| 1 | 25.5 img/s |
| 4 | 35.2 img/s |
| 16 | 42.5 img/s |
| 32 | 51.5 img/s |

- Batch 32는 Batch 1 대비 처리량이 약 2배 증가했지만 배치 지연 시간은 약 16.7배 증가했다.

### SavedModel 검증
- 입력 시그니처: `keras_tensor`, `(-1, 224, 224, 3)`, float32
- 출력 시그니처: `output_0`, `(-1, 1000)`, float32
- 원본 모델과 SavedModel 추론 결과 비교:
  - `allclose: True`
  - 최대 절대 오차: `2.8312206e-07`
- 모델 export 및 재로드 후에도 추론 결과가 허용 오차 범위 내에서 동일함을 확인했다.

### CLI 종료 코드
- 정상 종료: 0
- 파일·이미지 오류: 1
- 인자 오류: 2

### 실습 환경
- TensorFlow: 2.21.0
- Keras: 3.15.1
- GPU: 없음 (CPU 실행)

## 4. PyTorch vs TensorFlow

| 항목 | PyTorch ResNet50 | TensorFlow MobileNetV2 |
|---|---|---|
| 저장 방식 | state_dict + 모델 구조 코드 | `.keras` / SavedModel |
| 입력 레이아웃 | NCHW | NHWC |
| 전처리 | mean/std 정규화 | [-1, 1] |
| import 후 RSS | 약 676 MiB | 약 536 MiB |
| 로드 후 RSS 증가 | +118.67 MiB | +58.84 MiB |
| Batch 1 p50 | 290.67 ms | 43.93 ms (`tf.function`) |

※ 모델 구조와 설치 빌드가 다르므로 성능 우열을 직접 비교하는 자료는 아니다.

## 5. Infrastructure 연결
- SavedModel 시그니처는 서빙 API의 입력·출력 계약이므로 명확하게 관리해야 한다.
- `tf.function`의 초기 tracing 지연을 줄이기 위해 서버 시작 시 워밍업을 수행할 수 있다.
- 배치 크기를 높이면 처리량은 증가하지만 지연 시간도 커지므로 SLO에 맞는 배치 설정이 필요하다.
- 전처리 불일치는 오류 없이 추론 품질을 떨어뜨릴 수 있으므로 모델과 함께 버전 관리해야 한다.
- 모델 변경 시 기준 입력을 활용한 회귀 테스트와 카나리·섀도 배포가 필요하다.

## 6. 면접 포인트
- Keras 3의 `.keras`는 모델 저장·재학습용이고 SavedModel은 서빙용이다.
- SavedModel은 시그니처를 통해 입력·출력 규격을 정의하며, 모델 코드 없이 TensorFlow 런타임에서 추론할 수 있다.
- `tf.function`은 첫 호출의 tracing 비용이 발생하므로 서버 워밍업이 중요하다.
- 배치 크기는 처리량과 지연 시간 사이의 균형을 고려해 결정해야 한다.

## 7. 내 말로 3줄 요약
1. Keras 3에서 `.keras`는 편집·재학습용, SavedModel은 서빙용이며 시그니처가 서빙 API의 입력·출력 계약이 된다.
2. 모델마다 입력 레이아웃과 전처리가 다르므로 모델 버전과 함께 관리하고 기준 입력으로 결과를 검증해야 한다.
3. `tf.function`은 워밍업이 필요하며, 배치를 키우면 처리량은 증가하지만 지연 시간도 커지므로 적절한 균형이 중요하다.
