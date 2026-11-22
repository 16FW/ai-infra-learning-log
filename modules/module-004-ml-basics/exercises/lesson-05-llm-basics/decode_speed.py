import time, statistics, torch
from transformers import AutoTokenizer, AutoModelForCausalLM

tok = AutoTokenizer.from_pretrained("gpt2")
model = AutoModelForCausalLM.from_pretrained("gpt2").eval()

def make_input_ids(n_tokens):
    text = "The quick brown fox jumps over the lazy dog. " * 100
    return tok(text, return_tensors="pt")["input_ids"][:, :n_tokens]

def gen_time(input_ids, new_tokens):
    attn = torch.ones_like(input_ids)
    t0 = time.perf_counter()
    with torch.inference_mode():
        model.generate(
            input_ids=input_ids, attention_mask=attn,
            max_new_tokens=new_tokens, min_new_tokens=new_tokens,
            do_sample=False, pad_token_id=tok.eos_token_id,
        )
    return (time.perf_counter() - t0) * 1000   # ms

gen_time(make_input_ids(10), 5)    # 워밍업 1회 (결과 버림)

print("threads:", torch.get_num_threads())
for plen in (10, 400):
    ids = make_input_ids(plen)
    t1  = statistics.median(gen_time(ids, 1)  for _ in range(5))
    t33 = statistics.median(gen_time(ids, 33) for _ in range(5))
    per = (t33 - t1) / 32
    print(f"prompt={plen:4d}  first_token_ms={t1:.1f}  per_token_ms={per:.1f}  tokens/s={1000/per:.1f}")
