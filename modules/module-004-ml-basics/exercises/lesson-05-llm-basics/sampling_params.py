import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

tok = AutoTokenizer.from_pretrained("gpt2")
model = AutoModelForCausalLM.from_pretrained("gpt2")
model.eval()

prompt = "The future of AI infrastructure is"
inputs = tok(prompt, return_tensors="pt")

def gen(seed=None, **kw):
    if seed is not None:
        torch.manual_seed(seed)          # 호출 직전에 시드를 맞춘다
    with torch.inference_mode():
        out = model.generate(
            **inputs, max_new_tokens=25,
            pad_token_id=tok.eos_token_id, **kw
        )
    return tok.decode(out[0], skip_special_tokens=True)

# (1) greedy 2회
a = gen(do_sample=False); b = gen(do_sample=False)
print("(1) greedy 같음:", a == b)

# (2) 샘플링 2회 (시드 없음)
a = gen(do_sample=True, temperature=1.0)
b = gen(do_sample=True, temperature=1.0)
print("(2) 샘플링 같음:", a == b)

# (3) 샘플링 2회, 호출 직전마다 시드 재설정
a = gen(seed=42, do_sample=True)
b = gen(seed=42, do_sample=True)
print("(3) 시드 고정 같음:", a == b)

# (4) 온도별 (시드 고정)
for t in [0.2, 1.0, 1.5]:
    print(f"(4) T={t}:", gen(seed=42, do_sample=True, temperature=t))

# (5) top_k / top_p
print("(5) top_k=5:", gen(seed=42, do_sample=True, top_k=5))
print("(5) top_p=0.9:", gen(seed=42, do_sample=True, top_p=0.9, top_k=0))
