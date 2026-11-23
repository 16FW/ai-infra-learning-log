import pytest
import torch

from device_select import get_device


def fake_cuda(monkeypatch, available):
    monkeypatch.setattr(torch.cuda, "is_available", lambda: available)


def test_auto_without_cuda_is_cpu(monkeypatch):
    monkeypatch.delenv("DEVICE", raising=False)
    fake_cuda(monkeypatch, False)
    assert get_device().type == "cpu"


def test_auto_with_cuda_is_cuda(monkeypatch):
    monkeypatch.delenv("DEVICE", raising=False)
    fake_cuda(monkeypatch, True)
    assert get_device().type == "cuda"


def test_env_cpu_wins_even_if_cuda_available(monkeypatch):
    fake_cuda(monkeypatch, True)
    monkeypatch.setenv("DEVICE", "cpu")
    assert get_device().type == "cpu"


def test_env_cuda_without_cuda_raises(monkeypatch):
    fake_cuda(monkeypatch, False)
    monkeypatch.setenv("DEVICE", "cuda")
    with pytest.raises(RuntimeError):
        get_device()


def test_invalid_value_raises(monkeypatch):
    fake_cuda(monkeypatch, False)
    monkeypatch.setenv("DEVICE", "tpu")
    with pytest.raises(ValueError):
        get_device()


def test_arg_overrides_env(monkeypatch):
    fake_cuda(monkeypatch, True)
    monkeypatch.setenv("DEVICE", "cuda")
    assert get_device("cpu").type == "cpu"
