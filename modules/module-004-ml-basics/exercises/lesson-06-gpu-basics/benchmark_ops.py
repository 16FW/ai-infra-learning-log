import time, statistics, torch

def bench(fn, sync, n=10):
    for _ in range(2):                       # 워밍업 2회 버림
        fn()
    if torch.cuda.is_available():
        torch.cuda.synchronize()             # 워밍업이 끝났는지 확인하고 시작
    times = []
    for _ in range(n):
        if sync:
            torch.cuda.synchronize()
        t0 = time.perf_counter()
        fn()
        if sync:
            torch.cuda.synchronize()
        times.append((time.perf_counter() - t0) * 1000)
    if torch.cuda.is_available():
        torch.cuda.synchronize()             # 밀린 일을 비워서 다음 측정에 영향 안 주기
    return statistics.median(times)

assert torch.cuda.is_available(), "GPU 런타임이 아님"
dev = torch.device("cuda")
print("GPU:", torch.cuda.get_device_name(0))

rows = []
for N in (512, 2048, 4096):
    a_cpu = torch.randn(N, N)
    b_cpu = torch.randn(N, N)
    a_gpu, b_gpu = a_cpu.to(dev), b_cpu.to(dev)

    cpu_ms     = bench(lambda: a_cpu @ b_cpu, sync=False, n=5)
    gpu_sync   = bench(lambda: a_gpu @ b_gpu, sync=True)
    gpu_nosync = bench(lambda: a_gpu @ b_gpu, sync=False)
    h2d_ms     = bench(lambda: a_cpu.to(dev), sync=True)
    rows.append((N, cpu_ms, gpu_sync, gpu_nosync, h2d_ms))

print(f"{'N':>6} {'cpu_ms':>10} {'gpu_sync':>10} {'gpu_nosync':>11} {'h2d_ms':>9} {'speedup':>9} {'speedup+복사':>13}")
for N, c, gs, gn, h in rows:
    print(f"{N:>6} {c:>10.2f} {gs:>10.3f} {gn:>11.4f} {h:>9.3f} {c/gs:>9.1f} {c/(gs+2*h):>13.1f}")