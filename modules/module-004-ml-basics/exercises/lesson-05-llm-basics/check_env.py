import torch, transformers

print("torch:", torch.__version__)
print("transformers:", transformers.__version__)
print("CUDA 사용 가능:", torch.cuda.is_available())   # CPU 전용이니 False가 정상
print("CPU 스레드 수:", torch.get_num_threads())      # 속도 측정 때 항상 같이 기록
