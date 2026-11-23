import subprocess, torch, torchvision

MIB = 1024**2

def smi_used_mib():
    out = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
        text=True,
    )
    return int(out.strip().splitlines()[0])

def snap(tag):
    torch.cuda.synchronize()
    a = torch.cuda.memory_allocated() / MIB
    r = torch.cuda.memory_reserved() / MIB
    s = smi_used_mib()
    print(f"{tag:22s} allocated={a:9.1f}  reserved={r:9.1f}  smi_used={s:7d}  (MiB)")

# 1) 1GiB 텐서 3번 단계 할당, 삭제, empty_cache
snap("시작")
tensors = []
for i in range(3):
    tensors.append(torch.empty(1024**3 // 4, dtype=torch.float32, device="cuda"))   # 1GiB
    snap(f"1GiB x {i + 1} 할당")
tensors.clear()
snap("삭제 후")
torch.cuda.empty_cache()
snap("empty_cache 후")

# 2) 의도적 OOM
total = torch.cuda.get_device_properties(0).total_memory
try:
    t = torch.empty(int(total * 1.2) // 4, dtype=torch.float32, device="cuda")
except torch.cuda.OutOfMemoryError as e:
    print("OOM 발생:", str(e).splitlines()[0][:300])
print("프로세스 생존: 이 줄이 보이면 죽지 않았다")
snap("OOM 후")

# 3) ResNet50 batch별 피크 메모리
model = torchvision.models.resnet50(weights=torchvision.models.ResNet50_Weights.DEFAULT).eval().cuda()
for B in (1, 32, 128):
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    x = None
    try:
        x = torch.randn(B, 3, 224, 224, device="cuda")
        with torch.inference_mode():
            model(x)
        torch.cuda.synchronize()
        print(f"batch {B:3d}: peak={torch.cuda.max_memory_allocated() / MIB:8.1f} MiB")
    except torch.cuda.OutOfMemoryError:
        print(f"batch {B:3d}: OOM")
    x = None

# 4) 7B fp16 가중치가 이 GPU에 들어가는가
total_gib = total / 1024**3
weights_gib = 13.04
free_gib = total_gib - weights_gib
kv_per_token = 2 * 32 * 4096 * 2            # 2(K,V) x 32층 x 4096 x 2바이트(fp16)
print(f"GPU total {total_gib:.2f} GiB / 7B fp16 가중치 {weights_gib} GiB -> 여유 {free_gib:.2f} GiB")
print(f"토큰당 KV cache {kv_per_token / 1024:.0f} KiB -> 여유로 담을 수 있는 토큰 수(배치 1, 오버헤드 제외) 약 {free_gib * 1024**3 / kv_per_token:.0f}")