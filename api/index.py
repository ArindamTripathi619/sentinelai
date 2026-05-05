"""
Minimal Vercel serverless backend.
"""
from fastapi import FastAPI

app = FastAPI()

@app.get("/api/health")
async def health():
    return {"status": "ok", "message": "Backend is running"}

@app.get("/api/")
async def root():
    return {"message": "SentinelAI API"}



