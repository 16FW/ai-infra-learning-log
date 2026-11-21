
from pathlib import Path
import numpy as np
import onnxruntime as ort
from PIL import Image

# Lesson 2의 ResNet50 전처리 설정
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

IMAGE_PATHS = [
    Path("../lesson02/images/cat.jpg"),
    Path("../lesson02/images/car.jpg"),
    Path("../lesson02/images/dog.jpg"),
]


def preprocess_pil(image_path):
    """PIL + NumPy를 이용한 ResNet50 전처리"""

    image = Image.open(image_path).convert("RGB")
    width, height = image.size

    # Resize: 짧은 변을 232로 설정
    if width < height:
        new_width = 232
        new_height = int(232 * height / width)
    else:
        new_height = 232
        new_width = int(232 * width / height)

    image = image.resize(
        (new_width, new_height),
        Image.Resampling.BILINEAR
    )

    # Center Crop: 224 x 224
    left = int(round((new_width - 224) / 2.0))
    top = int(round((new_height - 224) / 2.0))

    image = image.crop(
        (left, top, left + 224, top + 224)
    )

    # HWC uint8 -> HWC float32 [0, 1]
    array = np.asarray(image, dtype=np.float32) / 255.0

    # Normalize
    array = (array - MEAN) / STD

    # HWC -> CHW
    array = np.transpose(array, (2, 0, 1))

    # CHW -> NCHW
    return np.expand_dims(array, axis=0).astype(np.float32)


def main():
    # ONNX Runtime 세션 생성
    session = ort.InferenceSession(
        "resnet50.onnx",
        providers=["CPUExecutionProvider"]
    )

    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name

    print("Available providers:", ort.get_available_providers())
    print("Session providers:", session.get_providers())

    # B1에서 저장한 torchvision 입력 및 PyTorch logits
    reference_inputs = np.load("resnet50_input.npy")
    reference_logits = np.load("resnet50_expected.npy")

    # B2: 동일 입력에 대한 ONNX 추론
    b2_actual = session.run(
        [output_name],
        {input_name: reference_inputs}
    )[0]

    print("\n=== B2 Reference ===")
    print("Input shape:", reference_inputs.shape)
    print("Output shape:", b2_actual.shape)
    print(
        "Overall conversion max error:",
        np.max(np.abs(reference_logits - b2_actual))
    )

    # 이미지별 비교
    for index, path in enumerate(IMAGE_PATHS):
        if not path.exists():
            raise FileNotFoundError(path)

        # B3: PIL + NumPy 전처리
        x = preprocess_pil(path)

        # ONNX 추론
        logits = session.run(
            [output_name],
            {input_name: x}
        )[0]

        # Top-1 / Top-5
        top5 = np.argsort(logits[0])[-5:][::-1]
        top1 = int(top5[0])

        # PyTorch 기준 결과
        expected = reference_logits[index]

        # B2: 동일 이미지의 변환 오차
        b2_error = np.max(
            np.abs(expected - b2_actual[index])
        )

        # B3: 전처리 차이까지 포함한 전체 오차
        b3_error = np.max(
            np.abs(expected - logits[0])
        )

        # 입력 단계의 전처리 차이
        input_error = np.max(
            np.abs(reference_inputs[index] - x[0])
        )

        # 동일 ONNX 모델에서 전처리 차이로 인한 logits 변화
        preprocessing_effect = np.max(
            np.abs(b2_actual[index] - logits[0])
        )

        # 평균 오차
        b3_mean_error = np.mean(
            np.abs(expected - logits[0])
        )

        print(f"\n=== {path.name} ===")
        print("Input shape:", x.shape)
        print("Input dtype:", x.dtype)

        print("\n[Prediction]")
        print("Top-1:", top1)
        print("Top-5:", top5)
        print("PyTorch Top-1:", int(np.argmax(expected)))
        print(
            "Top-1 match:",
            top1 == int(np.argmax(expected))
        )

        print("\n[Error]")
        print("B2 conversion max error:", b2_error)
        print("B3 total max error:", b3_error)
        print("B3 mean absolute error:", b3_mean_error)

        print("\n[Preprocessing Difference]")
        print("Input preprocessing max diff:", input_error)
        print("Preprocessing logits max diff:", preprocessing_effect)


if __name__ == "__main__":
    main()
