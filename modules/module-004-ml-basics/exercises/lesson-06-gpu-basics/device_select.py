import logging
import os

import torch

logger = logging.getLogger(__name__)
_ALLOWED = {"cpu", "cuda", "auto"}


def get_device(prefer: str | None = None) -> torch.device:
    """'cuda'를 명시했는데 GPU가 없으면 조용히 cpu로 가지 않고 RuntimeError를 낸다
    (GPU 서비스가 CPU로 느리게 도는 문제를 숨기지 않기 위해)."""
    value = prefer if prefer is not None else os.environ.get("DEVICE", "auto")
    value = value.strip().lower()
    if value not in _ALLOWED:
        raise ValueError(f"invalid device {value!r}; allowed: {sorted(_ALLOWED)}")

    if value == "cpu":
        device = torch.device("cpu")
    elif value == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("DEVICE=cuda requested but CUDA is not available")
        device = torch.device("cuda")
    else:  # auto
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    logger.info("selected device: %s (requested=%s)", device, value)
    return device
