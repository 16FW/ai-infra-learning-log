
import torch
import torch.nn as nn


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

    torch.onnx.export(
        model,
        (x,),
        "tiny_dyn.onnx",
        input_names=["input"],
        output_names=["output"],
        dynamo=True,
        dynamic_shapes=(
            {0: torch.export.Dim("batch_size")},
        )
    )

    print("Dynamic ONNX export 완료")


if __name__ == "__main__":
    main()
