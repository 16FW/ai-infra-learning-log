
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import tensorflow as tf
from tensorflow import keras


def build():
    # 입력 4개 -> 출력 3개
    model = keras.Sequential([
        keras.Input(shape=(4,)),
        keras.layers.Dense(3)
    ])
    return model


def get_directory_size(path):
    total = 0

    for root, dirs, files in os.walk(path):
        for filename in files:
            filepath = os.path.join(root, filename)
            total += os.path.getsize(filepath)

    return total


def main():
    # 재현 가능한 초기 가중치 설정
    keras.utils.set_random_seed(42)

    model = build()

    # TODO 2: 파라미터 개수 및 FP32 기준 크기
    params = model.count_params()
    fp32_bytes = params * 4

    print("[1. Model Information]")
    print(f"Parameters: {params:,}")
    print(f"FP32 size: {fp32_bytes:,} bytes")

    # TODO 3: Keras 모델 저장
    model.save("tiny.keras")

    # TODO 4: SavedModel export
    model.export(
        "tiny_savedmodel",
        format="tf_saved_model"
    )

    # TODO 5: 저장 파일 크기 비교
    keras_size = os.path.getsize("tiny.keras")
    savedmodel_size = get_directory_size("tiny_savedmodel")

    print("\n[2. Model Size]")
    print(f"tiny.keras: {keras_size:,} bytes")
    print(f"tiny_savedmodel: {savedmodel_size:,} bytes")

    # TODO 6: 기준 입력 예측
    x = tf.constant([[5.1, 3.5, 1.4, 0.2]])

    prediction = model(x, training=False)

    print("\n[3. Prediction]")
    print(prediction.numpy())


if __name__ == "__main__":
    main()
