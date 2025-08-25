from fastapi import FastAPI
app = FastAPI(title="Agent Executor", version="0.1.0")

@app.get("/healthz")
def healthz():
    return {"ok": True}
