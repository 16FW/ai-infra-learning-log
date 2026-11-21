
import onnxruntime as ort
import numpy as np

# ONNX 모델 로드
session = ort.InferenceSession(
    "tiny_dyn.onnx",
    providers=["CPUExecutionProvider"]
)

# 입력 이름을 모델에서 직접 확인
input_info = session.get_inputs()[0]
input_name = input_info.name

print("Input name:", input_name)
print("Input shape:", input_info.shape)

# 저장된 입력 및 기준 결과
x = np.load("x.npy").astype(np.float32)
expected = np.load("expected.npy")

# Batch 1 추론
actual = session.run(None, {input_name: x})[0]

print("\n=== Batch 1 ===")
print("Expected:", expected)
print("Actual:", actual)

print("allclose:", np.allclose(
    expected, actual, atol=1e-5
))

print("Max absolute error:",
      np.max(np.abs(expected - actual)))


# Batch 8 실험
x8 = np.repeat(x, 8, axis=0)

print("\n=== Batch 8 ===")
try:
    actual8 = session.run(None, {input_name: x8})[0]
    print("Success")
    print("Output shape:", actual8.shape)
except Exception as e:
    print("Failed")
    print("Error:", e)
