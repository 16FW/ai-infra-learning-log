
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import numpy as np
import tensorflow as tf
from tensorflow import keras


def main():

    print("===== R5. SavedModel Export =====")

    # ImageNet 가중치 모델 로드
    model = keras.applications.MobileNetV2(
        weights="imagenet",
        include_top=True,
        input_shape=(224, 224, 3)
    )

    # 테스트 입력
    x = tf.random.uniform(
        (1, 224, 224, 3),
        minval=-1,
        maxval=1
    )

    # 원본 모델 예측
    original_prediction = model(x, training=False)

    # SavedModel 내보내기
    model.export(
        "mobilenet_savedmodel",
        format="tf_saved_model"
    )

    print("\nExport completed.")

    # SavedModel 로드
    loaded = tf.saved_model.load(
        "mobilenet_savedmodel"
    )

    print("\nAvailable signatures:")
    print(loaded.signatures.keys())

    # 기본 serve 엔드포인트
    infer = loaded.signatures["serve"]

    print("\nInput signature:")
    print(infer.structured_input_signature)

    print("\nOutput signature:")
    print(infer.structured_outputs)

    # 실제 호출
    positional, keyword = infer.structured_input_signature

    if keyword:
        input_name = next(iter(keyword))
        restored_prediction = infer(**{input_name: x})
    else:
        restored_prediction = infer(x)

    # 결과 텐서
    output = next(iter(restored_prediction.values()))

    print("\n===== Prediction Comparison =====")

    print("Original shape:", original_prediction.shape)
    print("Restored shape:", output.shape)

    print(
        "Allclose:",
        np.allclose(
            original_prediction.numpy(),
            output.numpy(),
            atol=1e-5
        )
    )

    print(
        "Max absolute difference:",
        np.max(
            np.abs(
                original_prediction.numpy() - output.numpy()
            )
        )
    )


if __name__ == "__main__":
    main()
