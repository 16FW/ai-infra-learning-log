# 사용법:
#   python compare_models.py gpt2
#   python compare_models.py distilgpt2
#   python compare_models.py Qwen/Qwen2.5-0.5B-Instruct
# 가볍게 돌리고 싶을 때(느린 환경):
#   REPS=3 LONG=17 python compare_models.py Qwen/Qwen2.5-0.5B-Instruct

import os
import sys
import time
import statistics

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL = sys.argv[1]
REPS = int(os.environ.get("REPS", 5))     # 반복 횟수 (p50용)
LONG = int(os.environ.get("LONG", 33))    # 긴 쪽 생성 토큰 수


def rss_detail():
    d = {}
    with open("/proc/self/status") as f:
        for line in f:
            if line.startswith(("VmRSS", "RssAnon", "RssFile")):
                k, v = line.split(":")
                d[k] = int(v.split()[0]) / 1024   # kB -> MiB
    return d


# 1) 토크나이저, 모델 로드 (fp32 고정, 로드 시간 측정)
tok = AutoTokenizer.from_pretrained(MODEL)
pad_id = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id

t0 = time.perf_counter()
model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.float32).eval()
load_s = time.perf_counter() - t0

n_params = sum(p.numel() for p in model.parameters())

# 2) 프롬프트 10토큰짜리 입력
text = "The quick brown fox jumps over the lazy dog. " * 100
ids = tok(text, return_tensors="pt")["input_ids"][:, :10]
attn = torch.ones_like(ids)


def gen_time(n):
    t0 = time.perf_counter()
    with torch.inference_mode():
        model.generate(
            input_ids=ids, attention_mask=attn,
            max_new_tokens=n, min_new_tokens=n,
            do_sample=False, pad_token_id=pad_id,
        )
    return (time.perf_counter() - t0) * 1000   # ms


# 3) 워밍업 후 첫 generate 뒤 RSS, 속도 측정
print("워밍업 시작", flush=True)
gen_time(5)                                    # 결과 버림. 이때 가중치가 메모리로 올라옴
rss = rss_detail()
print("워밍업 끝, 측정 시작", flush=True)

t1 = statistics.median(gen_time(1) for _ in range(REPS))
print("T(1) 끝", flush=True)
tL = statistics.median(gen_time(LONG) for _ in range(REPS))
per = (tL - t1) / (LONG - 1)

# 4) config 읽기 (속성 이름은 모델마다 다르므로 먼저 출력해서 눈으로 확인)
print(model.config)

cfg = model.config
layers   = getattr(cfg, "num_hidden_layers", None) or getattr(cfg, "n_layer")
hidden   = getattr(cfg, "hidden_size", None) or getattr(cfg, "n_embd")
heads    = getattr(cfg, "num_attention_heads", None) or getattr(cfg, "n_head")
kv_heads = getattr(cfg, "num_key_value_heads", heads)   # 없으면 MHA로 간주
ctx      = getattr(cfg, "max_position_embeddings", None) or getattr(cfg, "n_positions")
head_dim = getattr(cfg, "head_dim", None) or hidden // heads

# 5) 토큰당 KV cache (fp32 = 4바이트): 2(K,V) x 레이어 x KV헤드 x 헤드크기 x 4
kv_per_token = 2 * layers * kv_heads * head_dim * 4

# 6) 결과 출력
print(f"\n[{MODEL}] threads={torch.get_num_threads()}  REPS={REPS}  LONG={LONG}")
print(f"파라미터 수: {n_params:,}")
print(f"로드 시간: {load_s:.2f} s")
print(f"첫 generate 후 RSS: VmRSS={rss['VmRSS']:.0f} RssAnon={rss['RssAnon']:.0f} RssFile={rss['RssFile']:.0f} MiB")
print(f"per_token_ms={per:.1f}  tokens/s={1000 / per:.1f}")
print(f"레이어={layers} hidden={hidden} heads={heads} kv_heads={kv_heads} head_dim={head_dim} ctx={ctx}")
print(f"토큰당 KV cache(fp32): {kv_per_token:,} B = {kv_per_token / 1024:.1f} KiB")
