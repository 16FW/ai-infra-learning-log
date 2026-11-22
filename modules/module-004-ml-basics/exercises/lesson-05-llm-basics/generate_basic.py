import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL = "gpt2"
tok = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(MODEL)
model.eval()

prompt = "Kubernetes is"
inputs = tok(prompt, return_tensors="pt")
print("keys:", list(inputs.keys()))

with torch.inference_mode():
    out_ids = model.generate(
        **inputs,
        max_new_tokens=30,
        do_sample=False,
        pad_token_id=tok.eos_token_id,
    )

text = tok.decode(out_ids[0], skip_special_tokens=True)
print(text)

prompt_len = inputs["input_ids"].shape[1]
print("프롬프트 토큰:", prompt_len)
print("out_ids.shape:", out_ids.shape)
print("새로 생성된 토큰:", out_ids.shape[1] - prompt_len)

cfg = model.config
print("n_layer:", cfg.n_layer)
print("n_head:", cfg.n_head)
print("n_embd:", cfg.n_embd)
print("n_positions:", cfg.n_positions)
print("vocab_size:", cfg.vocab_size)
