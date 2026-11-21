
import torch
import torch.nn as nn
import numpy as np


class TinyNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(4, 3)

    def forward(self, x):
        return self.fc(x)


def main():
    torch.manual_seed(0)

    model = TinyNet().eval()
    x = torch.randn(1, 4)

    # ONNX export
    torch.onnx.export(
        model,
        (x,),
        "tiny.onnx",
        input_names=["input"],
        output_names=["output"],
        dynamo=True
    )

    # PyTorch 기준 예측값 저장
    with torch.no_grad():
        expected = model(x)

    np.save("x.npy", x.numpy())
    np.save("expected.npy", expected.numpy())

    print("ONNX export 완료")
    print("Input shape:", tuple(x.shape))
    print("Expected:", expected.numpy())


if __name__ == "__main__":
    main()
