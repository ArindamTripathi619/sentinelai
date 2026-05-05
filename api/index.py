"""
Minimal Vercel serverless backend.
"""
from fastapi import FastAPI

app = FastAPI()

@app.get("/api/health")
async def health():
    return {"status": "ok"}

@app.get("/api/")
async def root():
    return {"message": "SentinelAI"}



