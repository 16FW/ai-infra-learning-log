import os, signal, sys, time

MODE = os.environ.get("MODE", "A")

def on_term(signum, frame):
    print("SIGTERM 받음, 정리 후 종료", flush=True)
    sys.exit(0)

if MODE == "B":
    signal.signal(signal.SIGTERM, on_term)

print(f"start pid={os.getpid()} mode={MODE}", flush=True)
i = 0
while True:
    i += 1
    print(f"tick {i}", flush=True)
    time.sleep(1)
