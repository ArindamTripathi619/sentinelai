# SentinelAI — FastAPI Backend Entry Point
# Atul is responsible for this file and all imports below

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(
    title="SentinelAI",
    description="Behavioral Intelligence Platform for Campus Event Ecosystems",
    version="1.0.0"
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Route Imports ---
# Uncomment as each module is completed

# from auth import router as auth_router
# from users import router as users_router
# from alerts import router as alerts_router
# from analytics import router as analytics_router
# from scoring import router as scoring_router

# app.include_router(auth_router, prefix="/api", tags=["Auth"])
# app.include_router(users_router, prefix="/api", tags=["Users"])
# app.include_router(alerts_router, prefix="/api", tags=["Alerts"])
# app.include_router(analytics_router, prefix="/api", tags=["Analytics"])
# app.include_router(scoring_router, prefix="/api", tags=["Scoring"])


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


# --- Stub routes (replace with real routers as work is completed) ---

@app.post("/api/register")
async def register_stub():
    # TODO: Atul implements this in auth.py
    return {"message": "stub — not yet implemented"}


@app.post("/api/login")
async def login_stub():
    # TODO: Atul implements this in auth.py
    return {"message": "stub — not yet implemented"}


@app.post("/api/otp/send")
async def otp_send_stub():
    # TODO: Atul implements this in auth.py
    return {"message": "stub — not yet implemented"}


@app.post("/api/otp/verify")
async def otp_verify_stub():
    # TODO: Atul implements this in auth.py
    return {"message": "stub — not yet implemented"}


@app.get("/api/users")
async def users_stub():
    # TODO: Atul implements this — returns user list for dashboard
    return {"total": 0, "users": []}


@app.get("/api/users/{user_id}/timeline")
async def timeline_stub(user_id: str):
    # TODO: Atul implements this
    return {"user_id": user_id, "timeline": []}


@app.get("/api/alerts")
async def alerts_stub():
    # TODO: Wire to Akash's rules engine output
    return {"alerts": []}


@app.get("/api/analytics/summary")
async def summary_stub():
    # TODO: Atul implements aggregation queries
    return {
        "total_users": 0,
        "flagged_today": 0,
        "bot_waves_detected": 0,
        "quarantined": 0,
        "blocked": 0,
        "avg_trust_score": 0
    }


@app.get("/api/analytics/velocity")
async def velocity_stub():
    return {"window": "1h", "data": [], "spike_detected": False}


@app.get("/api/analytics/trust-distribution")
async def trust_dist_stub():
    return {"bands": [], "total": 0}


@app.post("/api/score")
async def score_stub():
    # TODO: Akash implements the scoring pipeline here
    return {"trust_score": 100, "triggered_rules": [], "recommendation": "allow"}
