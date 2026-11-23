import sys, time

def status():
    d = {}
    with open("/proc/self/status") as f:
        for line in f:
            k = line.split(":")[0]
            if k in ("VmRSS", "RssAnon", "RssFile", "VmSwap"):
                d[k] = int(line.split()[1]) // 1024
    return d

target = int(sys.argv[1])
chunks = []
while len(chunks) * 10 < target:
    c = bytearray(10 * 1024 * 1024)
    for i in range(0, len(c), 4096):
        c[i] = 1
    chunks.append(c)
    time.sleep(0.2)
print(f"allocated={len(chunks) * 10}MB {status()}", flush=True)
time.sleep(600)
