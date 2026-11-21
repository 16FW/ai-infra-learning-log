import numpy as np
import onnxruntime as ort

# 저장된 입력 및 PyTorch 기준 결과
x = np.load("resnet50_input.npy")
expected = np.load("resnet50_expected.npy")

# ONNX Runtime 세션 생성
session = ort.InferenceSession(
    "resnet50.onnx",
    providers=["CPUExecutionProvider"]
)

print("Available providers:", ort.get_available_providers())
print("Session providers:", session.get_providers())

# ONNX 추론
input_name = session.get_inputs()[0].name
output_name = session.get_outputs()[0].name

actual = session.run(
    [output_name],
    {input_name: x}
)[0]

# 오차 계산
diff = np.abs(expected - actual)
max_error = np.max(diff)
mean_error = np.mean(diff)

# 허용 오차 설정
rtol = 1e-3
atol = 1e-5

is_close = np.allclose(
    expected,
    actual,
    rtol=rtol,
    atol=atol
)

# Top-1 비교
expected_top1 = np.argmax(expected, axis=1)
actual_top1 = np.argmax(actual, axis=1)

top1_match = expected_top1 == actual_top1

print("\n=== ONNX Validation ===")
print("Input shape:", x.shape)
print("Expected shape:", expected.shape)
print("Actual shape:", actual.shape)

print("\n=== Error ===")
print("Max absolute error:", max_error)
print("Mean absolute error:", mean_error)
print(f"Tolerance: rtol={rtol}, atol={atol}")
print("allclose:", is_close)

print("\n=== Top-1 Comparison ===")
print("PyTorch:", expected_top1)
print("ONNX:", actual_top1)
print("Per-image match:", top1_match)
print("All top-1 match:", np.all(top1_match))

print("\n=== Tolerance Policy ===")
print(
    "FP32 연산 순서 및 최적화에 따른 미세한 수치 차이를 허용하되, "
    "예측 결과의 유사성을 검증하기 위해 rtol=1e-3, atol=1e-5를 사용한다."
)
