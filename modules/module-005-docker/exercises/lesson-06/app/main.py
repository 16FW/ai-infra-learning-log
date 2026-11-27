import os
import redis
from fastapi import FastAPI

app = FastAPI()
r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, decode_responses=True)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/hits")
def hits():
    return {"hits": r.incr("hits")}
