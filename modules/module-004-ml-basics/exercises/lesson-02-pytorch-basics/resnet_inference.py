import argparse
from pathlib import Path
from urllib.parse import urlparse

import torch
from PIL import Image
from torchvision.models import ResNet50_Weights, resnet50


WEIGHTS = ResNet50_Weights.IMAGENET1K_V2


def read_rss_bytes():
    """현재 프로세스의 RSS를 /proc/self/status에서 읽습니다."""
    with open("/proc/self/status", encoding="utf-8") as file:
        for line in file:
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) * 1024

    raise RuntimeError("VmRSS 항목을 찾지 못했습니다.")


def load_model():
    """import 시점에는 실행하지 않고, 호출할 때 모델을 만듭니다."""
    model = resnet50(weights=WEIGHTS)
    model = model.to(device="cpu", dtype=torch.float32)
    model.eval()
    return model


def prepare_image(image_path):
    """파일을 열고, 가중치에 맞는 전처리를 수행합니다."""
    with Image.open(image_path) as image:
        image = image.convert("RGB")
        tensor = WEIGHTS.transforms()(image)

    return tensor


def predict_topk(model, batch, topk=5):
    with torch.no_grad():
        logits = model(batch)
        probabilities = torch.softmax(logits, dim=1)
        scores, indices = probabilities.topk(topk, dim=1)

    categories = WEIGHTS.meta["categories"]

    # 이 함수에서는 배치 첫 번째 이미지의 결과를 반환합니다.
    return [
        (categories[index], score)
        for score, index in zip(
            scores[0].tolist(),
            indices[0].tolist(),
        )
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("images", nargs="+")
    args = parser.parse_args()

    print("[R1: 모델 로딩과 크기]")

    # torch와 torchvision import가 완료된 이후를 기준으로 합니다.
    rss_before = read_rss_bytes()

    model = load_model()

    rss_after = read_rss_bytes()

    parameter_count = sum(
        parameter.numel()
        for parameter in model.parameters()
    )

    fp32_bytes = parameter_count * 4

    parameter_bytes = sum(
        parameter.numel() * parameter.element_size()
        for parameter in model.parameters()
    )

    buffer_bytes = sum(
        buffer.numel() * buffer.element_size()
        for buffer in model.buffers()
    )

    checkpoint_name = Path(urlparse(WEIGHTS.url).path).name
    checkpoint_path = (
        Path(torch.hub.get_dir())
        / "checkpoints"
        / checkpoint_name
    )

    print("가중치:", WEIGHTS)
    print("device:", next(model.parameters()).device)
    print("파라미터 개수:", f"{parameter_count:,}")
    print("fp32 계산값:", f"{fp32_bytes:,}", "bytes")
    print("실제 파라미터 데이터:", f"{parameter_bytes:,}", "bytes")
    print("버퍼 데이터:", f"{buffer_bytes:,}", "bytes")

    print("체크포인트:", checkpoint_path)

    if checkpoint_path.is_file():
        file_bytes = checkpoint_path.stat().st_size
        print("체크포인트 크기:", f"{file_bytes:,}", "bytes")
        print(
            "파일 크기 - 파라미터 크기:",
            f"{file_bytes - parameter_bytes:,}",
            "bytes",
        )

    print("로딩 전 RSS:", f"{rss_before:,}", "bytes")
    print("로딩 후 RSS:", f"{rss_after:,}", "bytes")
    print(
        "RSS 증가:",
        f"{rss_after - rss_before:,}",
        "bytes",
    )
    print(
        "RSS 증가:",
        f"{(rss_after - rss_before) / 1024**2:.2f}",
        "MiB",
    )

    print("\n전처리 설정:")
    print(WEIGHTS.transforms())

    for image_path in args.images:
        print(f"\n[R2/R3: {image_path}]")

        tensor = prepare_image(image_path)
        batch = tensor.unsqueeze(0)

        print("변환 후 shape:", tuple(tensor.shape))
        print("변환 후 dtype:", tensor.dtype)
        print("배치 shape:", tuple(batch.shape))

        for rank, (name, score) in enumerate(
            predict_topk(model, batch, topk=5),
            start=1,
        ):
            print(f"{rank}. {name}: {score:.2%}")


if __name__ == "__main__":
    main()
