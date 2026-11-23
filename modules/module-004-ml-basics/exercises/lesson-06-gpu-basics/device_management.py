import torch
import torch.nn as nn

dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("선택된 장치:", dev)

# (1) 텐서의 .to()
x = torch.randn(1000, 1000)
print("x.device (이동 전):", x.device)
x.to(dev)                                    # 결과를 받지 않고 호출
print("x.to(dev) 호출 후 원본 x.device:", x.device)
y = x.to(dev)                                # 새 변수에 받음
print("y.device:", y.device, "/ 원본 x.device:", x.device)

# (2) 장치 불일치 오류
try:
    z = y + torch.randn(1000, 1000)          # GPU 텐서 + CPU 텐서
except Exception as e:
    print("오류 타입:", type(e).__name__)
    print("메시지:", e)

# (3) 모델의 .to()
lin = nn.Linear(10, 10)
print("모델 이동 전:", next(lin.parameters()).device)
ret = lin.to(dev)                            # 반환값은 따로 받았지만 lin도 확인
print("이동 후(lin):", next(lin.parameters()).device, "/ lin is ret:", lin is ret)

# (4) 큰 텐서의 메모리 변화
def show(tag):
    a = torch.cuda.memory_allocated() / 1024**2
    r = torch.cuda.memory_reserved() / 1024**2
    print(f"{tag:14s} allocated={a:8.1f} MiB  reserved={r:8.1f} MiB")

show("시작")
big = torch.empty(2 * 1024**3 // 4, dtype=torch.float32, device=dev)   # 2GiB
show("할당 후")
del big
show("del 후")
torch.cuda.empty_cache()
show("empty_cache 후")