import time

import torch

assert torch.cuda.is_available(), "CUDA not available"
device = torch.device("cuda")
print(f"device: {torch.cuda.get_device_name(0)}, capability: {torch.cuda.get_device_capability(0)}")

dtype = torch.float16
size = 4096

a = torch.randn(size, size, device=device, dtype=dtype)
b = torch.randn(size, size, device=device, dtype=dtype)

# warmup
for _ in range(3):
    c = a @ b
torch.cuda.synchronize()

start = time.perf_counter()
iters = 20
for _ in range(iters):
    c = a @ b
torch.cuda.synchronize()
elapsed = time.perf_counter() - start
print(f"matmul {size}x{size} fp16: {elapsed/iters*1000:.2f} ms/iter avg over {iters} iters")

conv = torch.nn.Conv2d(320, 320, kernel_size=3, padding=1, dtype=dtype, device=device)
x = torch.randn(2, 320, 64, 64, device=device, dtype=dtype)

for _ in range(3):
    y = conv(x)
torch.cuda.synchronize()

start = time.perf_counter()
for _ in range(iters):
    y = conv(x)
torch.cuda.synchronize()
elapsed = time.perf_counter() - start
print(f"conv2d 320ch 64x64 fp16: {elapsed/iters*1000:.2f} ms/iter avg over {iters} iters")
