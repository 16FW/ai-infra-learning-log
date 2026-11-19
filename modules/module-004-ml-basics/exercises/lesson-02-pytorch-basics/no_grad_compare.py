import torch

from tiny_net import TinyNet


def main():
    # 1. 모델 구조 생성
    model = TinyNet()

    # 2. 4-A에서 저장한 상태 읽기
    state = torch.load(
        "tiny.pt",
        map_location="cpu",
        weights_only=True,
    )

    # 3. 모델에 상태 적용
    model.load_state_dict(state)
    model.eval()

    # 4. 동일한 입력 준비
    # shape: [배치 1개, 입력 특성 4개]
    x = torch.tensor(
        [[1.0, 2.0, 3.0, 4.0]],
        dtype=torch.float32,
    )

    # 5. 일반 실행
    y_normal = model(x)

    # 6. no_grad 실행
    with torch.no_grad():
        y_no_grad = model(x)

    # 7. 결과 관찰
    print("[일반 실행]")
    print(y_normal)
    print("requires_grad:", y_normal.requires_grad)
    print("grad_fn:", y_normal.grad_fn)

    print("\n[no_grad 실행]")
    print(y_no_grad)
    print("requires_grad:", y_no_grad.requires_grad)
    print("grad_fn:", y_no_grad.grad_fn)

    print(
        "\n두 출력의 숫자가 같은가?:",
        torch.equal(y_normal, y_no_grad),
    )


if __name__ == "__main__":
    main()
