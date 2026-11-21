
from pathlib import Path
import numpy as np
import onnxruntime as ort

# 현재 스크립트 기준 상위 디렉터리
BASE_DIR = Path(__file__).resolve().parent.parent

model_path = BASE_DIR / "tiny.onnx"
input_path = BASE_DIR / "x.npy"
expected_path = BASE_DIR / "expected.npy"

# ONNX Runtime으로 모델 로드
session = ort.InferenceSession(
    str(model_path),
    providers=["CPUExecutionProvider"]
)

# 입력 정보 확인
input_info = session.get_inputs()[0]
input_name = input_info.name

# 데이터 로드
x = np.load(input_path).astype(np.float32)
expected = np.load(expected_path)

# 추론
actual = session.run(None, {input_name: x})[0]

# 결과 비교
print("Input shape:", x.shape)
print("Output shape:", actual.shape)
print("Expected:", expected)
print("Actual:", actual)

print("allclose:", np.allclose(
    expected, actual, atol=1e-5
))

print("Max absolute error:",
      np.max(np.abs(expected - actual)))

# RSS 확인
with open("/proc/self/status") as f:
    for line in f:
        if line.startswith("VmRSS:"):
            print("RSS:", line.strip())
            break
