from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import os
from dotenv import load_dotenv
import auth
import users
import alerts
import analytics
import scoring
from database import init_db

load_dotenv()

# Try to initialize DB, but don't fail if it can't connect yet
try:
    init_db()
except Exception as e:
    import sys
    print(f"Warning: Database initialization failed at startup: {e}", file=sys.stderr)
    # Continue anyway - the database might connect on first request

app = FastAPI(
    title="SentinelAI",
    description="Behavioral Intelligence Platform for Campus Event Ecosystems",
    version="1.0.0"
)

from database import engine
import models

models.Base.metadata.create_all(bind=engine)

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
    allowed_hosts=["localhost", "127.0.0.1", "*.localhost", "*.vercel.app", *extra_allowed_hosts],
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
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(scoring.router, prefix="/api/score", tags=["Scoring"])

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

@app.get("/diagnostics")
def diagnostics():
    """Diagnostic endpoint to check environment and dependencies."""
    import sys
    return {
        "python_version": sys.version,
        "database_url_set": bool(os.getenv("DATABASE_URL")),
        "supabase_url": os.getenv("SUPABASE_URL", "NOT SET"),
        "service_role_key_set": bool(os.getenv("SUPABASE_SERVICE_ROLE_KEY")),
        "message": "All systems OK"
    }
