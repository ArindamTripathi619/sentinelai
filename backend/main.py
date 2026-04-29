from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import auth
from database import init_db

load_dotenv()

# Initialize DB
init_db()

app = FastAPI(
    title="SentinelAI",
    description="Behavioral Intelligence Platform for Campus Event Ecosystems",
    version="1.0.0"
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:5173"), "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Route Imports ---
app.include_router(auth.router, prefix="/api", tags=["Auth & Core"])

@app.get("/")
def root():
    return {
        "service": "SentinelAI",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
def health():
    return {"status": "ok"}
