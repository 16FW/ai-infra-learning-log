import os

path = "/data/count.txt"
os.makedirs("/data", exist_ok=True)
n = int(open(path).read()) if os.path.exists(path) else 0
n += 1
open(path, "w").write(str(n))
print(f"실행 횟수: {n}")
