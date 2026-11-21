import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import numpy as np
import tensorflow as tf
import onnx
import onnxruntime as ort

SAVED_MODEL_DIR = "../lesson03/mobilenet_savedmodel"
ONNX_PATH = "mobilenetv2.onnx"

# 1. TensorFlow SavedModel 로드
loaded = tf.saved_model.load(SAVED_MODEL_DIR)
infer = loaded.signatures["serve"]

# 2. ONNX 모델 정보 확인
onnx_model = onnx.load(ONNX_PATH)
onnx.checker.check_model(onnx_model)

session = ort.InferenceSession(
    ONNX_PATH,
    providers=["CPUExecutionProvider"]
)

print("=== Model Information ===")
print("TensorFlow signature:", "serve")
print("ONNX input:", session.get_inputs()[0].name)
print("ONNX input shape:", session.get_inputs()[0].shape)
print("ONNX output:", session.get_outputs()[0].name)
print("ONNX output shape:", session.get_outputs()[0].shape)
print("ONNX providers:", session.get_providers())

# 3. 동일한 입력 생성
rng = np.random.default_rng(42)
x = rng.random((1, 224, 224, 3), dtype=np.float32)

# 4. TensorFlow 추론
tf_result = infer(
    keras_tensor=tf.convert_to_tensor(x)
)
tf_output = next(iter(tf_result.values())).numpy()

# 5. ONNX Runtime 추론
input_name = session.get_inputs()[0].name
output_name = session.get_outputs()[0].name

ort_output = session.run(
    [output_name],
    {input_name: x}
)[0]

# 6. 결과 비교
abs_error = np.abs(tf_output - ort_output)

print("\n=== Output Comparison ===")
print("Input shape:", x.shape)
print("TensorFlow output shape:", tf_output.shape)
print("ONNX output shape:", ort_output.shape)
print("Max absolute error:", np.max(abs_error))
print("Mean absolute error:", np.mean(abs_error))

print("\n=== Prediction Comparison ===")
tf_top1 = np.argmax(tf_output, axis=1)
ort_top1 = np.argmax(ort_output, axis=1)

print("TensorFlow Top-1:", tf_top1)
print("ONNX Top-1:", ort_top1)
print("Top-1 match:", np.array_equal(tf_top1, ort_top1))

print("\n=== Numerical Validation ===")
print("allclose:", np.allclose(
    tf_output,
    ort_output,
    rtol=1e-3,
    atol=1e-5
))
