from pathlib import Path
import os
import numpy as np
import torch
import torchvision
from PIL import Image
from torchvision.models import resnet50, ResNet50_Weights

print("PyTorch:", torch.__version__)
print("Torchvision:", torchvision.__version__)

torch.manual_seed(42)
device = torch.device("cpu")

weights = ResNet50_Weights.IMAGENET1K_V2
model = resnet50(weights=weights)
model.eval()
model.to(device)

preprocess = weights.transforms()
print("Preprocessing:", preprocess)

image_paths = [
    Path("../lesson02/images/cat.jpg"),
    Path("../lesson02/images/car.jpg"),
    Path("../lesson02/images/dog.jpg"),
]

inputs = []

for path in image_paths:
    if not path.exists():
        raise FileNotFoundError(f"이미지를 찾을 수 없습니다: {path}")

    image = Image.open(path).convert("RGB")
    inputs.append(preprocess(image))

x = torch.stack(inputs).to(device)

with torch.no_grad():
    logits = model(x)

np.save("resnet50_input.npy", x.cpu().numpy())
np.save("resnet50_expected.npy", logits.cpu().numpy())

torch.onnx.export(
    model,
    x,
    "resnet50.onnx",
    input_names=["input"],
    output_names=["logits"],
    dynamic_axes={
        "input": {0: "batch_size"},
        "logits": {0: "batch_size"},
    },
    opset_version=18,
    dynamo=False,
)

onnx_size = os.path.getsize("resnet50.onnx")
pth_size = 102_540_417

print("\n=== Export Result ===")
print("Input shape:", tuple(x.shape))
print("Logits shape:", tuple(logits.shape))
print("ONNX size:", f"{onnx_size:,} bytes")
print("Reference .pth size:", f"{pth_size:,} bytes")
print("Size difference:", f"{onnx_size - pth_size:+,} bytes")
print("ONNX larger:", onnx_size > pth_size)
