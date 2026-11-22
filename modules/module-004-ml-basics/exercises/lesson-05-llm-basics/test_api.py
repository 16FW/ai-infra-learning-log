import threading
import time
import requests

BASE = "http://127.0.0.1:8000"


def wait_ready(timeout=120):
    t0, last = time.time(), None
    while time.time() - t0 < timeout:
        try:
            code = requests.get(f"{BASE}/ready", timeout=2).status_code
        except requests.exceptions.ConnectionError:
            code = "연결 거부"
        if code != last:
            print(f"/ready -> {code}  ({time.time() - t0:.1f}s)")
            last = code
        if code == 200:
            return
        time.sleep(0.3)
    raise SystemExit("ready 안 됨")


def post(body):
    return requests.post(f"{BASE}/generate", json=body, timeout=120)


wait_ready()

print("--- 정상 ---")
r = post({"prompt": "Kubernetes is", "max_new_tokens": 20})
print(r.status_code, r.json())

print("--- 실패 3종 ---")
cases = {
    "빈 prompt": {"prompt": ""},
    "max_new_tokens 상한 초과": {"prompt": "hi", "max_new_tokens": 100},
    "컨텍스트 초과": {"prompt": "hello " * 1100, "max_new_tokens": 30},
}
for name, body in cases.items():
    r = post(body)
    print(name, r.status_code, str(r.json())[:120])

print("--- 동시성 ---")
body = {"prompt": "The future of AI infrastructure is", "max_new_tokens": 30}
t0 = time.perf_counter()
post(body)
single = (time.perf_counter() - t0) * 1000
print(f"1건: {single:.0f} ms")

results = []


def worker():
    t0 = time.perf_counter()
    post(body)
    results.append((time.perf_counter() - t0) * 1000)


threads = [threading.Thread(target=worker) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()
print("4건 각각(ms):", [round(x) for x in sorted(results)])
print(f"1건 대비 평균 {sum(results) / 4 / single:.1f}배, 최대 {max(results) / single:.1f}배")
