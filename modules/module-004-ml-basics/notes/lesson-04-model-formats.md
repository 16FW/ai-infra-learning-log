# Lesson 04. Model Formats: ONNX 변환, 검증, ONNX Runtime

## 핵심 개념
- ONNX는 프레임워크 중립적인 모델 표현이다. 연산 그래프 + 가중치(initializer) + 입출력 이름/shape + opset 버전이 들어 있다. 학습 프레임워크와 서빙 런타임을 분리한다.
- 그래프는 연산자(operator) 단위로 표현된다(Linear → Gemm 1노드). opset 버전이 런타임 호환성을 정하므로 서빙 런타임 버전을 맞춰야 한다.
- export 시 예시 입력의 shape이 기본적으로 반영된다. 배치를 가변으로 사용하려면 dynamic_shapes 또는 dynamic_axes를 지정해야 한다.
- 단일 protobuf 파일에는 2GB 상한이 있어 큰 모델은 external data로 가중치를 분리해야 한다.
- 변환의 한계: 지원하지 않는 연산에서 실패할 수 있고, 수치 오차가 생기며, 변환 도구와 프레임워크 버전 조합에 따라 동작이 달라질 수 있다.

## 동작 원리
- torch.onnx.export()는 PyTorch 모델을 연산 그래프로 캡처해 ONNX 그래프로 변환한다.
- ONNX Runtime은 InferenceSession(path).run(None, {입력이름: ndarray}) 방식으로 추론한다. 입력 이름과 shape은 get_inputs()로 확인한다.
- 변환 오차와 전처리 오차를 분리해서 확인한다. 동일한 입력 텐서로 비교하면 변환 오차를, 원본 이미지부터 비교하면 전처리 오차까지 포함한 결과를 확인할 수 있다.
- np.allclose로 출력값의 수치적 일치 여부를 검증하며, rtol과 atol을 명시해 허용 오차 기준을 정한다.

## 실습에서 한 것
- TinyNet을 ONNX로 변환하고 정적·동적 배치 입력의 차이를 확인했다. 동적 배치 설정으로 다양한 batch size에서 추론할 수 있음을 검증했다.
- ONNX Runtime만 설치된 환경에서 PyTorch 없이 모델 추론이 가능함을 확인했다.
- ResNet50을 ONNX로 변환했다. ONNX 파일은 102,146,393B로 원본 .pth 파일보다 394,024B 작았다. 변환 최대 오차는 6.91e-6이었고, 이미지 3장의 Top-1 예측이 모두 일치했다.
- PIL+NumPy 전처리 결과를 torchvision과 비교한 결과 최대 차이는 0.0이었으며, Top-1 예측도 일치했다.
- CPU 성능 비교에서 ONNX Runtime의 p50 지연시간은 PyTorch보다 batch 1에서 약 33.7%, batch 4에서 약 26.1%, batch 16에서 약 36.4% 낮았다. 단, batch 16의 p95는 ONNX Runtime이 약간 높았다.
- PyTorch와 ONNX Runtime의 스레드 수를 각각 1개로 설정해 비교했다.
- ONNX Runtime 세션 생성에는 약 2.35초가 소요됐으며, 첫 추론 호출은 약 91.66ms였다.
- ONNX Runtime 전용 가상환경의 용량은 전체 개발 환경의 약 2.1%였다.
- TensorFlow SavedModel인 MobileNetV2를 tf2onnx로 ONNX 변환했다. 변환 환경은 TensorFlow 2.21.0, Keras 3.15.1, tf2onnx 1.17.0, ONNX 1.23.2이며 opset은 18이다. 변환 최대 오차는 4.47e-7이었고 Top-1 예측이 일치했다.

## Infrastructure 연결
- 서빙 이미지에는 onnxruntime + numpy(+pillow)만 넣고, 학습·변환은 별도 파이프라인에서 수행해 서빙 환경의 의존성과 용량을 줄인다.
- 변환과 검증(동일 입력 비교, 허용 오차, Top-1 일치)을 CI 단계에 포함하고, 검증을 통과한 모델만 모델 레지스트리에 등록한다.
- opset, ONNX Runtime, 변환 도구, TensorFlow/Keras 버전 조합을 기록하고 고정한다.
- ONNX Runtime 세션 생성은 초기화 비용이 발생하므로 서버 시작 시 세션을 한 번 생성하고 워밍업한 뒤 재사용한다.
- 큰 모델은 external data로 가중치가 분리될 수 있으므로 관련 파일을 함께 버전 관리하고 배포해야 한다.

## 면접 포인트
- ONNX를 사용하는 이유: 학습 프레임워크와 서빙 런타임의 분리, 다양한 환경에서의 모델 실행.
- ONNX의 trade-off: 변환 실패 가능성, 수치 오차, 도구 및 버전 호환성, 변환 이후 디버깅의 어려움.
- 변환 후 검증 방법: 동일 입력 비교, 허용 오차 기준 설정, Top-1 일치 여부 확인, 전처리 오차 분리.

## 내 말로 3줄 요약
1. ONNX는 프레임워크 중립적인 모델 표현으로, PyTorch나 TensorFlow에서 학습한 모델을 ONNX Runtime으로 실행할 수 있어 서빙 환경을 가볍게 구성할 수 있다.
2. 모델 변환은 export로 끝나는 것이 아니라 동일 입력에 대한 출력 비교와 허용 오차 검증까지 수행해야 하며, 전처리 오차와 변환 오차를 구분해야 한다.
3. 실제 서빙 환경에서는 동적 입력 shape 설정, opset 및 런타임 호환성 관리, 세션 재사용과 워밍업 등을 고려해야 한다.
