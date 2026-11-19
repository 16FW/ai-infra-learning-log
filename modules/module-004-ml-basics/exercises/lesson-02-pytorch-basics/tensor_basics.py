import torch

a = torch.ones(2, 3)
b = torch.ones(2, 3, dtype=torch.float16)
c = torch.ones(2, 3, dtype=torch.int8)

print(a.dtype, a.element_size())
print(b.dtype, b.element_size())
print(c.dtype, c.element_size())
print(a.shape, a.T.shape)
print((a + b).dtype)
print(torch.zeros(1000, 1000).element_size() * torch.zeros(1000, 1000).nelement())
