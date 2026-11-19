import argparse
from pathlib import Path
import sys

from PIL import UnidentifiedImageError

from resnet_inference import (
    WEIGHTS,
    load_model,
    predict_topk,
    prepare_image,
)


def main():
    parser = argparse.ArgumentParser(
        description="ResNet50으로 이미지의 top-k 클래스를 출력합니다."
    )

    parser.add_argument("image", type=Path)
    parser.add_argument("--topk", type=int, default=5)

    args = parser.parse_args()

    class_count = len(WEIGHTS.meta["categories"])

    if not 1 <= args.topk <= class_count:
        parser.error(
            f"--topk는 1~{class_count} 사이여야 합니다."
        )

    if not args.image.is_file():
        print(
            f"오류: 이미지 파일이 없습니다: {args.image}",
            file=sys.stderr,
        )
        return 2

    # 잘못된 파일이라면 모델을 로드하기 전에 중단합니다.
    try:
        tensor = prepare_image(args.image)

    except UnidentifiedImageError:
        print(
            f"오류: 이미지 형식을 인식할 수 없습니다: {args.image}",
            file=sys.stderr,
        )
        return 2

    except (OSError, ValueError, SyntaxError) as error:
        print(
            f"오류: 이미지를 읽을 수 없습니다: {error}",
            file=sys.stderr,
        )
        return 2

    try:
        model = load_model()
        batch = tensor.unsqueeze(0)

        results = predict_topk(
            model,
            batch,
            topk=args.topk,
        )

    except Exception as error:
        # CLI 경계에서 모델 로딩·추론 실패를 사용자 메시지로 변환합니다.
        print(
            f"오류: 모델 로딩 또는 추론에 실패했습니다: {error}",
            file=sys.stderr,
        )
        return 1

    for rank, (name, score) in enumerate(results, start=1):
        print(f"{rank}. {name}: {score:.2%}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
