import time, statistics, torch, torchvision

def make_model(device, dtype):
    m = torchvision.models.resnet50(weights=torchvision.models.ResNet50_Weights.DEFAULT)
    m = m.eval()
    if dtype == torch.float16:
        m = m.half()                 # CPU에서 변환한 뒤 GPU로 옮김(GPU에 fp32가 잠깐 올라가지 않게)
    return m.to(device)

def run(model, x, sync, n, warmup=3):
    with torch.inference_mode():
        for _ in range(warmup):      # 워밍업 3회 버림
            model(x)
        if sync:
            torch.cuda.synchronize()
        times = []
        for _ in range(n):
            if sync:
                torch.cuda.synchronize()
            t0 = time.perf_counter()
            model(x)
            if sync:
                torch.cuda.synchronize()
            times.append((time.perf_counter() - t0) * 1000)
    return statistics.median(times)

print("GPU:", torch.cuda.get_device_name(0), "/ CPU 스레드:", torch.get_num_threads())
configs = [("cpu", torch.float32), ("cuda", torch.float32), ("cuda", torch.float16)]
print(f"{'device':>6} {'dtype':>5} {'batch':>5} {'p50_ms':>9} {'img/s':>8} {'peak_MiB':>9}")

for dev_name, dtype in configs:
    device = torch.device(dev_name)
    model = make_model(device, dtype)
    for B in (1, 8, 32):
        x = torch.randn(B, 3, 224, 224, device=device, dtype=dtype)
        if dev_name == "cuda":
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()
        ms = run(model, x, sync=(dev_name == "cuda"), n=(5 if dev_name == "cpu" else 20))
        peak = f"{torch.cuda.max_memory_allocated() / 1024**2:9.1f}" if dev_name == "cuda" else "        -"
        dt = "fp32" if dtype == torch.float32 else "fp16"
        print(f"{dev_name:>6} {dt:>5} {B:>5} {ms:>9.2f} {B / (ms / 1000):>8.1f} {peak}")
    del model
    if dev_name == "cuda":
        torch.cuda.empty_cache()