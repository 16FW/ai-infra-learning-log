from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok", "version": 3}

@app.post("/predict")
def predict(x: float):
    return {"y": x * 2}
