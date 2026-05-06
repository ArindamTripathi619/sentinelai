from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import os
from dotenv import load_dotenv
from fastapi.responses import FileResponse
from pathlib import Path
import auth
import users
import alerts
import analytics
import scoring

load_dotenv()

app = FastAPI(
    title="SentinelAI",
    description="Behavioral Intelligence Platform for Campus Event Ecosystems",
    version="1.0.0"
)

import models

# --- Security Headers Middleware ---
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        # Prevent clickjacking attacks
        response.headers["X-Frame-Options"] = "DENY"
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Enable XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # Enforce HTTPS (set max-age to 1 year)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # Set SameSite cookies for CSRF protection
        response.headers["Set-Cookie"] = "SameSite=Strict"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# --- Trusted Host Middleware (prevents Host header injection) ---
extra_allowed_hosts = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "").split(",")
    if host.strip()
]
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.localhost", "*.onrender.com", *extra_allowed_hosts],
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:5173"), "http://localhost:3000"],
    allow_origin_regex=r"https://.*\.onrender\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Route Imports ---
app.include_router(auth.router, prefix="/api", tags=["Auth & Core"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(scoring.router, prefix="/api/score", tags=["Scoring"])

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
FRONTEND_INDEX = FRONTEND_DIST / "index.html"

@app.get("/")
def root():
    if FRONTEND_INDEX.exists():
        return FileResponse(FRONTEND_INDEX)
    return {
        "service": "SentinelAI",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/{path_name:path}")
def spa_fallback(path_name: str):
    if path_name.startswith("api/") or path_name == "api":
        raise HTTPException(status_code=404, detail="Not Found")

    if FRONTEND_INDEX.exists():
        return FileResponse(FRONTEND_INDEX)

    raise HTTPException(status_code=404, detail="Not Found")
