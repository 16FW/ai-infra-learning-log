import torch

print("torch:", torch.__version__)
print("torch가 빌드된 CUDA:", torch.version.cuda)
print("cuda 사용 가능:", torch.cuda.is_available())

if torch.cuda.is_available():
    props = torch.cuda.get_device_properties(0)
    print("장치 이름:", torch.cuda.get_device_name(0))
    print("compute capability:", f"{props.major}.{props.minor}")
    print("total_memory(GiB):", round(props.total_memory / 1024**3, 2))
    print("memory_allocated(MiB):", torch.cuda.memory_allocated() / 1024**2)
    print("memory_reserved(MiB):", torch.cuda.memory_reserved() / 1024**2)