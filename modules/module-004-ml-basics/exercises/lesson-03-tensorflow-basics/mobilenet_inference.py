
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import glob
import time
import resource

import numpy as np
import tensorflow as tf
from tensorflow import keras

from PIL import Image


def get_rss():
    """Linux VmRSS를 MiB로 반환"""
    with open("/proc/self/status", "r") as f:
        for line in f:
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) / 1024

    return 0


def preprocess_image(path):
    """Resize 232 + Center Crop 224 + MobileNetV2 전처리"""

    image = Image.open(path).convert("RGB")

    # 짧은 변 기준 232로 resize
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

    # Center Crop 224
    left = (new_width - 224) // 2
    top = (new_height - 224) // 2

    image = image.crop((
        left,
        top,
        left + 224,
        top + 224
    ))

    image_array = np.asarray(image, dtype=np.float32)

    # MobileNetV2 전용 전처리
    image_array = keras.applications.mobilenet_v2.preprocess_input(
        image_array
    )

    return np.expand_dims(image_array, axis=0)


def main():
    print("===== R1. Model Loading =====")

    # TensorFlow import 이후 기준 RSS
    baseline_rss = get_rss()

    print(f"Baseline RSS: {baseline_rss:.2f} MiB")

    # 모델 로드 시간 측정
    start = time.perf_counter()

    model = keras.applications.MobileNetV2(
        weights="imagenet",
        include_top=True,
        input_shape=(224, 224, 3)
    )

    load_time = time.perf_counter() - start

    loaded_rss = get_rss()
    rss_increase = loaded_rss - baseline_rss

    print(f"Load time: {load_time:.3f} sec")
    print(f"Loaded RSS: {loaded_rss:.2f} MiB")
    print(f"RSS increase: {rss_increase:.2f} MiB")

    # 파라미터 수
    params = model.count_params()
    fp32_size = params * 4

    print(f"\nParameters: {params:,}")
    print(f"FP32 size: {fp32_size:,} bytes")
    print(f"FP32 size: {fp32_size / (1024**2):.2f} MiB")

    # 실제 다운로드 가중치 확인
    weight_files = glob.glob(
        os.path.expanduser("~/.keras/models/*mobilenet*v2*")
    )

    print("\n===== Weight Files =====")

    for path in weight_files:
        print(
            os.path.basename(path),
            f"{os.path.getsize(path):,} bytes",
            f"({os.path.getsize(path) / (1024**2):.2f} MiB)"
        )

    # 추론 기준 이미지
    print("\n===== R2. Preprocessing =====")

    for filename in ["cat.jpg", "car.jpg", "dog.jpg"]:
        path = os.path.join("images", filename)

        x = preprocess_image(path)

        print(f"\n{filename}")
        print("Shape:", x.shape)
        print("Dtype:", x.dtype)
        print("Min:", x.min())
        print("Max:", x.max())

        # R3 추론
        prediction = model.predict(x, verbose=0)

        top5 = keras.applications.mobilenet_v2.decode_predictions(
            prediction,
            top=5
        )[0]

        print("\nTop-5:")

        for rank, (class_id, label, score) in enumerate(top5, 1):
            print(
                f"{rank}. {label}: {score * 100:.2f}% "
                f"({class_id})"
            )


if __name__ == "__main__":
    main()
