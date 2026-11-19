from pathlib import Path

import torch
import torch.nn as nn


class TinyNet(nn.Module):
    def __init__(self):
        super().__init__()

        # 입력 특성 4개 → 출력 특성 3개
        self.fc = nn.Linear(4, 3)

    def forward(self, x):
        return self.fc(x)


def main():
    # 실습 조건 고정
    torch.set_default_dtype(torch.float32)
    torch.manual_seed(0)

    print("PyTorch 버전:", torch.__version__)

    # --------------------------------
    # 4-A. 모델 생성
    # --------------------------------
    model = TinyNet()

    print("\n[4-A-1] state_dict의 키와 shape")

    for name, tensor in model.state_dict().items():
        print(
            name,
            "shape =", tuple(tensor.shape),
            "dtype =", tensor.dtype,
        )

    # --------------------------------
    # 파라미터 개수와 바이트 수
    # --------------------------------
    print("\n[4-A-2] 파라미터 개수와 데이터 크기")

    total_params = 0
    total_bytes = 0

    for name, parameter in model.named_parameters():
        count = parameter.numel()
        element_bytes = parameter.element_size()
        data_bytes = count * element_bytes

        total_params += count
        total_bytes += data_bytes

        print(
            name,
            "개수 =", count,
            "원소당 바이트 =", element_bytes,
            "데이터 바이트 =", data_bytes,
        )

    print("총 파라미터 개수:", total_params)
    print("총 파라미터 데이터:", total_bytes, "bytes")

    # --------------------------------
    # state_dict 저장
    # --------------------------------
    print("\n[4-A-3] state_dict 저장")

    torch.save(model.state_dict(), "tiny.pt")

    file_bytes = Path("tiny.pt").stat().st_size

    print("tiny.pt 실제 크기:", file_bytes, "bytes")
    print("계산값과 차이:", file_bytes - total_bytes, "bytes")

    # --------------------------------
    # 새 모델에 복원
    # --------------------------------
    print("\n[4-A-4] 새 인스턴스에 복원")

    restored = TinyNet()

    state = torch.load(
        "tiny.pt",
        map_location="cpu",
        weights_only=True,
    )

    load_result = restored.load_state_dict(state)
    print("복원 결과:", load_result)

    # 배치 2개, 샘플마다 입력 특성 4개
    x = torch.tensor([
        [1.0, 2.0, 3.0, 4.0],
        [4.0, 3.0, 2.0, 1.0],
    ])

    model.eval()
    restored.eval()

    with torch.no_grad():
        original_output = model(x)
        restored_output = restored(x)

    print("입력 shape:", tuple(x.shape))
    print("원래 모델 출력:")
    print(original_output)

    print("복원 모델 출력:")
    print(restored_output)

    print(
        "torch.equal:",
        torch.equal(original_output, restored_output),
    )

    # --------------------------------
    # 4-B에서 사용할 전체 모델 파일 저장
    # --------------------------------
    torch.save(model, "tiny_full.pt")
    print("\n전체 모델을 tiny_full.pt에 저장했습니다.")

    # --------------------------------
    # 4-C. no_grad 유무 비교
    # --------------------------------
    print("\n[4-C] no_grad 유무 비교")

    normal_output = model(x)

    with torch.no_grad():
        no_grad_output = model(x)

    print("\n일반 실행:")
    print(normal_output)
    print("requires_grad:", normal_output.requires_grad)
    print("grad_fn:", normal_output.grad_fn)

    print("\nno_grad 실행:")
    print(no_grad_output)
    print("requires_grad:", no_grad_output.requires_grad)
    print("grad_fn:", no_grad_output.grad_fn)

    print(
        "\n두 출력의 숫자가 같은가?:",
        torch.equal(normal_output, no_grad_output),
    )


if __name__ == "__main__":
    main()

