
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import time
import numpy as np
import tensorflow as tf
from tensorflow import keras


def load_model():
    return keras.applications.MobileNetV2(
        weights="imagenet",
        include_top=True,
        input_shape=(224, 224, 3)
    )


def measure_latency(fn, x, warmup=5, iterations=30):
    # 워밍업
    for _ in range(warmup):
        result = fn(x)

    if hasattr(result, "numpy"):
        result.numpy()

    # 실제 측정
    times = []

    for _ in range(iterations):
        start = time.perf_counter()

        result = fn(x)

        # 비동기 실행 가능성을 고려해 동기화
        if hasattr(result, "numpy"):
            result.numpy()

        times.append((time.perf_counter() - start) * 1000)

    return (
        np.percentile(times, 50),
        np.percentile(times, 95),
        len(x) / (np.mean(times) / 1000)
    )


def main():
    model = load_model()

    # 랜덤 입력으로 호출 방식 비교
    x = tf.random.uniform(
        (1, 224, 224, 3),
        minval=-1,
        maxval=1
    )

    print("===== R4. Calling Method Comparison =====")

    # 1. Keras predict
    p50, p95, throughput = measure_latency(
        lambda x: model.predict(x, verbose=0),
        x
    )

    print(
        f"predict: p50={p50:.2f} ms | "
        f"p95={p95:.2f} ms | "
        f"throughput={throughput:.2f} img/s"
    )

    # 2. Direct call
    direct_fn = lambda x: model(x, training=False)

    p50, p95, throughput = measure_latency(
        direct_fn,
        x
    )

    print(
        f"direct: p50={p50:.2f} ms | "
        f"p95={p95:.2f} ms | "
        f"throughput={throughput:.2f} img/s"
    )

    # 3. tf.function
    @tf.function
    def graph_fn(x):
        return model(x, training=False)

    # 첫 호출 별도 측정
    start = time.perf_counter()
    first_result = graph_fn(x)
    first_result.numpy()

    first_call = (time.perf_counter() - start) * 1000

    print(f"tf.function first call: {first_call:.2f} ms")

    # 이후 반복 호출
    p50, p95, throughput = measure_latency(
        graph_fn,
        x
    )

    print(
        f"tf.function steady: p50={p50:.2f} ms | "
        f"p95={p95:.2f} ms | "
        f"throughput={throughput:.2f} img/s"
    )

    print("\n===== Batch Throughput =====")

    for batch_size in [1, 4, 16, 32]:

        batch = tf.random.uniform(
            (batch_size, 224, 224, 3),
            minval=-1,
            maxval=1
        )

        # 그래프 실행 방식으로 배치 측정
        p50, p95, throughput = measure_latency(
            graph_fn,
            batch,
            warmup=5,
            iterations=30
        )

        print(
            f"batch={batch_size:2d} | "
            f"p50={p50:.2f} ms | "
            f"p95={p95:.2f} ms | "
            f"throughput={throughput:.2f} img/s"
        )


if __name__ == "__main__":
    main()
