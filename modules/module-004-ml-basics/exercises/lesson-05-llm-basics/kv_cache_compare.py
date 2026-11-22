import time, statistics, torch
from transformers import AutoTokenizer, AutoModelForCausalLM

tok = AutoTokenizer.from_pretrained("gpt2")
model = AutoModelForCausalLM.from_pretrained("gpt2").eval()

text = "The quick brown fox jumps over the lazy dog. " * 100
ids = tok(text, return_tensors="pt")["input_ids"][:, :10]      # 프롬프트 10토큰
attn = torch.ones_like(ids)

def run(use_cache, n):
    t0 = time.perf_counter()
    with torch.inference_mode():
        out = model.generate(
            input_ids=ids, attention_mask=attn,
            max_new_tokens=n, min_new_tokens=n,
            do_sample=False, use_cache=use_cache,
            pad_token_id=tok.eos_token_id,
        )
    ms = (time.perf_counter() - t0) * 1000
    return ms, tok.decode(out[0], skip_special_tokens=True)

run(True, 5)                                   # 워밍업 (버림)

times, texts = {}, {}
for uc in (True, False):
    for n in (20, 40, 80):
        ts = []
        for _ in range(3):
            ms, txt = run(uc, n)
            ts.append(ms)
        times[(uc, n)] = statistics.median(ts)
        texts[(uc, n)] = txt

print("use_cache   n=20      n=40      n=80   (ms)")
for uc in (True, False):
    print(f"{str(uc):9s}", *[f"{times[(uc, n)]:8.0f}" for n in (20, 40, 80)])

for n in (20, 40, 80):
    print(f"n={n} 출력 동일:", texts[(True, n)] == texts[(False, n)])

for uc in (True, False):
    print(f"use_cache={uc}: time(80)/time(20) = {times[(uc, 80)] / times[(uc, 20)]:.2f}")
