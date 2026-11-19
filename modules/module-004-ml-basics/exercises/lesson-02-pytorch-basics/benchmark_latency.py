
import time
import numpy as np
import torch
from torchvision.models import resnet50, ResNet50_Weights

def measure(model, batch_size, warmup, iters):
    x = torch.randn(batch_size, 3, 224, 224)
    times = []

    # TODO 1: Warmup
    with torch.no_grad():
        for _ in range(warmup):
            model(x)

        # TODO 2: 추론 시간 측정
        for _ in range(iters):
            start = time.perf_counter()
            model(x)
            end = time.perf_counter()
            times.append(end - start)

    return times


def main():
    # TODO 3: 모델 로드 및 평가 모드
    weights = ResNet50_Weights.IMAGENET1K_V2
    model = resnet50(weights=weights)
    model.eval()

    for bs, iters in [(1, 50), (4, 20), (16, 20), (32, 20)]:
        times = measure(model, bs, warmup=5, iters=iters)

        # TODO 4: p50, p95, 처리량 계산
        p50 = np.percentile(times, 50)
        p95 = np.percentile(times, 95)

        throughput = bs / p50

        print(
            f"batch={bs:2d} | "
            f"p50={p50*1000:.2f} ms | "
            f"p95={p95*1000:.2f} ms | "
            f"throughput={throughput:.2f} img/s"
        )


if __name__ == "__main__":
    main()
