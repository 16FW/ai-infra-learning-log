import torch

from tiny_net import TinyNet


def main():
    model = TinyNet()

    print("클래스의 모듈:", TinyNet.__module__)

    torch.save(model, "tiny_full2.pt")
    print("tiny_full2.pt 저장 완료")


if __name__ == "__main__":
    main()
