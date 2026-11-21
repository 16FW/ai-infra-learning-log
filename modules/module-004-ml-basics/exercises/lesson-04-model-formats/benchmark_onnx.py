import time
import numpy as np
import torch
import onnxruntime as ort
from torchvision.models import resnet50, ResNet50_Weights

# =====================================
# 1. 실행 환경 설정
# =====================================

torch.set_num_threads(1)
torch.set_num_interop_threads(1)

THREADS = 1
BATCH_SIZES = [1, 4, 16]

print("PyTorch:", torch.__version__)
print("ONNX Runtime:", ort.__version__)
print("Available providers:", ort.get_available_providers())

# =====================================
# 2. PyTorch 모델 준비
# =====================================

weights = ResNet50_Weights.IMAGENET1K_V2
model = resnet50(weights=weights)
model.eval()
model.cpu()

# =====================================
# 3. ONNX Runtime 세션 생성 시간 측정
# =====================================

options = ort.SessionOptions()
options.intra_op_num_threads = THREADS
options.inter_op_num_threads = THREADS
options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL

start = time.perf_counter()

session = ort.InferenceSession(
    "resnet50.onnx",
    sess_options=options,
    providers=["CPUExecutionProvider"]
)

session_create_time = (time.perf_counter() - start) * 1000

input_name = session.get_inputs()[0].name
output_name = session.get_outputs()[0].name

print("\n=== Runtime Configuration ===")
print("PyTorch threads:", torch.get_num_threads())
print("ORT intra-op threads:", options.intra_op_num_threads)
print("ORT inter-op threads:", options.inter_op_num_threads)
print("Session providers:", session.get_providers())
print("ORT session creation:", f"{session_create_time:.2f} ms")

# =====================================
# 4. 입력 데이터 준비
# =====================================

base = np.load("resnet50_input.npy").astype(np.float32)

def make_batch(batch_size):
    samples = [
        base[[i % len(base)]]
        for i in range(batch_size)
    ]
    return np.ascontiguousarray(
        np.concatenate(samples, axis=0)
    )

# =====================================
# 5. ORT 첫 호출 시간 측정
# =====================================

first_input = make_batch(1)

start = time.perf_counter()

first_output = session.run(
    [output_name],
    {input_name: first_input}
)[0]

first_call_time = (time.perf_counter() - start) * 1000

print("ORT first call:", f"{first_call_time:.2f} ms")

# =====================================
# 6. 벤치마크 함수
# =====================================

def benchmark_pytorch(x, warmup=5, repeats=20):
    tensor = torch.from_numpy(x)

    with torch.no_grad():
        # Warm-up
        for _ in range(warmup):
            model(tensor)

        times = []

        for _ in range(repeats):
            start = time.perf_counter()
            model(tensor)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

    return np.array(times)


def benchmark_ort(x, warmup=5, repeats=20):
    # Warm-up
    for _ in range(warmup):
        session.run(
            [output_name],
            {input_name: x}
        )

    times = []

    for _ in range(repeats):
        start = time.perf_counter()

        session.run(
            [output_name],
            {input_name: x}
        )

        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)

    return np.array(times)


# =====================================
# 7. Batch별 성능 측정
# =====================================

print("\n=== Benchmark Results ===")

for batch_size in BATCH_SIZES:
    x = make_batch(batch_size)

    # Batch 16의 측정 시간이 길 수 있어 반복 횟수 조정
    repeats = 20 if batch_size == 1 else (
        15 if batch_size == 4 else 10
    )

    pt_times = benchmark_pytorch(
        x,
        warmup=5,
        repeats=repeats
    )

    ort_times = benchmark_ort(
        x,
        warmup=5,
        repeats=repeats
    )

    # 출력 결과 일치 여부 확인
    with torch.no_grad():
        pt_output = model(torch.from_numpy(x)).numpy()

    ort_output = session.run(
        [output_name],
        {input_name: x}
    )[0]

    max_error = np.max(np.abs(pt_output - ort_output))

    # 지연시간 및 처리량 계산
    pt_p50 = np.percentile(pt_times, 50)
    pt_p95 = np.percentile(pt_times, 95)
    pt_throughput = batch_size / (np.sum(pt_times) / 1000)

    ort_p50 = np.percentile(ort_times, 50)
    ort_p95 = np.percentile(ort_times, 95)
    ort_throughput = batch_size / (np.sum(ort_times) / 1000)

    print(f"\n--- Batch {batch_size} ---")

    print("[PyTorch]")
    print(f"p50: {pt_p50:.2f} ms")
    print(f"p95: {pt_p95:.2f} ms")
    print(f"Throughput: {pt_throughput:.2f} img/s")

    print("[ONNX Runtime]")
    print(f"p50: {ort_p50:.2f} ms")
    print(f"p95: {ort_p95:.2f} ms")
    print(f"Throughput: {ort_throughput:.2f} img/s")

    print("[Validation]")
    print(f"Max absolute error: {max_error:.8e}")
