import traceback

import torch


def main():
    print("PyTorch 버전:", torch.__version__, flush=True)

    # --------------------------------
    # 가. state_dict 파일 읽기
    # --------------------------------
    print("\n[가] state_dict 기본 로딩", flush=True)

    try:
        state = torch.load("tiny.pt")

        print("성공:", type(state), flush=True)

        for name, tensor in state.items():
            print(
                name,
                tuple(tensor.shape),
                flush=True,
            )

    except Exception:
        traceback.print_exc()

    # --------------------------------
    # 나-1. 전체 모델 기본 로딩
    # --------------------------------
    print("\n[나-1] 전체 모델 기본 로딩", flush=True)

    try:
        model = torch.load("tiny_full.pt")
        print("성공:", type(model), flush=True)

    except Exception:
        traceback.print_exc()

    # --------------------------------
    # 나-2. 직접 만든 파일에 한해
    # weights_only=False로 비교
    # --------------------------------
    print(
        "\n[나-2] 전체 모델 weights_only=False 로딩",
        flush=True,
    )

    try:
        model = torch.load(
            "tiny_full.pt",
            weights_only=False,
        )

        print("성공:", type(model), flush=True)

    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    main()

