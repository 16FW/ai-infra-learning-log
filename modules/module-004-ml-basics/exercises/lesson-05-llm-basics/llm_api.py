import threading
import time
from contextlib import asynccontextmanager

import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_NAME = "gpt2"
MAX_NEW_TOKENS_LIMIT = 64
state = {"ready": False}
gen_lock = threading.Lock()


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1)
    max_new_tokens: int = Field(default=30, ge=1, le=MAX_NEW_TOKENS_LIMIT)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    seed: int | None = None


def load_model():
    tok = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, dtype=torch.float32).eval()
    state["tok"] = tok
    state["model"] = model
    state["ctx"] = model.config.n_positions
    warm = tok("warmup", return_tensors="pt")          # 워밍업 1회
    with torch.inference_mode():
        model.generate(**warm, max_new_tokens=5, do_sample=False,
                       pad_token_id=tok.eos_token_id)
    state["ready"] = True                              # 맨 마지막에 ready


@asynccontextmanager
async def lifespan(app):
    threading.Thread(target=load_model, daemon=True).start()
    yield
    state["ready"] = False
    state.pop("model", None)
    state.pop("tok", None)


app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}                            # 살아 있으면 200


@app.get("/ready")
def ready():
    if not state["ready"]:
        raise HTTPException(status_code=503, detail="model loading")
    return {"status": "ready", "model": MODEL_NAME}


@app.post("/generate")
def generate(req: GenerateRequest):
    if not state["ready"]:
        raise HTTPException(status_code=503, detail="model loading")
    tok, model = state["tok"], state["model"]

    enc = tok(req.prompt, return_tensors="pt")
    prompt_tokens = enc["input_ids"].shape[1]
    if prompt_tokens + req.max_new_tokens > state["ctx"]:
        raise HTTPException(
            status_code=400,
            detail=f"prompt_tokens({prompt_tokens}) + max_new_tokens({req.max_new_tokens}) "
                   f"exceeds context {state['ctx']}",
        )

    kwargs = dict(max_new_tokens=req.max_new_tokens, pad_token_id=tok.eos_token_id)
    if req.temperature == 0:
        kwargs["do_sample"] = False                    # greedy
    else:
        kwargs.update(do_sample=True, temperature=req.temperature)

    t0 = time.perf_counter()
    with gen_lock:                                     # 한 번에 하나씩 (시드도 안전)
        if req.seed is not None:
            torch.manual_seed(req.seed)
        with torch.inference_mode():
            out = model.generate(**enc, **kwargs)
    latency_ms = (time.perf_counter() - t0) * 1000     # 대기 시간 포함

    new_ids = out[0][prompt_tokens:]
    return {
        "text": tok.decode(new_ids, skip_special_tokens=True),
        "prompt_tokens": prompt_tokens,
        "new_tokens": len(new_ids),
        "latency_ms": round(latency_ms, 1),
        "model": MODEL_NAME,
    }
