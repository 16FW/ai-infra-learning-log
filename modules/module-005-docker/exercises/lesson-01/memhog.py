import time

def rss_mb():
    with open("/proc/self/status") as f:
        for line in f:
            if line.startswith("VmRSS"):
                return int(line.split()[1]) // 1024

chunks = []
while True:
    chunk = bytearray(10 * 1024 * 1024)       # 10MB
    for i in range(0, len(chunk), 4096):      # 페이지(4KiB)마다 1바이트씩 써서 실제 할당을 보장
        chunk[i] = 1
    chunks.append(chunk)
    print(f"allocated={len(chunks) * 10}MB RSS={rss_mb()}MB", flush=True)
    time.sleep(0.2)
