import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

def rss_detail():
    d = {}
    with open("/proc/self/status") as f:
        for line in f:
            if line.startswith(("VmRSS", "RssAnon", "RssFile")):
                k, v = line.split(":")
                d[k] = int(v.split()[0]) / 1024   # kB -> MiB
    return d

def show(label):
    d = rss_detail()
    print(f"{label:10s} VmRSS={d['VmRSS']:.1f}  RssAnon={d['RssAnon']:.1f}  RssFile={d['RssFile']:.1f}  (MiB)")

tok = AutoTokenizer.from_pretrained("gpt2")
model = AutoModelForCausalLM.from_pretrained("gpt2", dtype=torch.float32).eval()
show("로드 직후")

inputs = tok("The future of AI infrastructure is", return_tensors="pt")

def run():
    with torch.inference_mode():
        model.generate(**inputs, max_new_tokens=30, do_sample=False,
                       pad_token_id=tok.eos_token_id)

run()
show("생성 1회 후")
for _ in range(9):
    run()
show("생성 10회 후")
