
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import sys
import argparse

import numpy as np
import tensorflow as tf
from tensorflow import keras

from PIL import Image, UnidentifiedImageError


def preprocess_image(path):
    image = Image.open(path).convert("RGB")

    width, height = image.size

    if width < height:
        new_width = 232
        new_height = int(height * 232 / width)
    else:
        new_height = 232
        new_width = int(width * 232 / height)

    image = image.resize(
        (new_width, new_height),
        Image.Resampling.BILINEAR
    )

    left = (new_width - 224) // 2
    top = (new_height - 224) // 2

    image = image.crop((
        left,
        top,
        left + 224,
        top + 224
    ))

    x = np.asarray(image, dtype=np.float32)

    x = keras.applications.mobilenet_v2.preprocess_input(x)

    return np.expand_dims(x, axis=0)


def main():

    parser = argparse.ArgumentParser(
        description="MobileNetV2 Image Classification CLI"
    )

    parser.add_argument(
        "image",
        help="Path to input image"
    )

    args = parser.parse_args()

    # 파일 존재 확인
    if not os.path.isfile(args.image):
        print(f"Error: File not found: {args.image}", file=sys.stderr)
        return 1

    # 이미지 전처리
    try:
        x = preprocess_image(args.image)

    except (
        UnidentifiedImageError,
        OSError,
        ValueError
    ) as e:
        print(f"Error: Invalid image: {e}", file=sys.stderr)
        return 1

    # 모델 로드
    try:
        model = keras.applications.MobileNetV2(
            weights="imagenet",
            include_top=True,
            input_shape=(224, 224, 3)
        )

        prediction = model.predict(x, verbose=0)

    except Exception as e:
        print(f"Error: Model inference failed: {e}", file=sys.stderr)
        return 1

    # Top-5 결과
    results = keras.applications.mobilenet_v2.decode_predictions(
        prediction,
        top=5
    )[0]

    print(f"Image: {args.image}")
    print("Top-5 predictions:")

    for rank, (class_id, label, score) in enumerate(results, 1):
        print(
            f"{rank}. {label}: {score * 100:.2f}% "
            f"({class_id})"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
