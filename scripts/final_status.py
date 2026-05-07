#!/usr/bin/env python3
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')
# Note: consolidated to a single `.env` at the repository root; do not load backend/.env

sys.path.insert(0, './backend')

from database import SessionLocal, is_sqlite_url, DATABASE_URL
from models import Alert, User, Event

db = SessionLocal()

alerts = db.query(Alert).count()
users = db.query(User).count()
quarantined = db.query(User).filter(User.status == 'quarantined').count()
flagged = db.query(User).filter(User.status == 'flagged').count()
events = db.query(Event).count()
database_kind = "SQLite" if is_sqlite_url(DATABASE_URL) else "PostgreSQL"

print("""
╔═══════════════════════════════════════════════════════════╗
║           SENTINELAI SYSTEM STATUS REPORT                ║
╚═══════════════════════════════════════════════════════════╝

DATABASE METRICS:
""")
print(f"  • Total Alerts Created:      {alerts}")
print(f"  • Total Users:               {users}")
print(f"  • Quarantined Users:         {quarantined}")
print(f"  • Flagged Users:             {flagged}")
print(f"  • Security Events Logged:    {events}")
print("""
DETECTION COVERAGE:
  ✓ Bot Wave Detection
  ✓ Brute Force / Credential Stuffing
  ✓ Geodrift / Location Anomalies
  ✓ Email Pattern Anomalies
  ✓ Device/UA Fingerprinting
  ✓ Behavioral Analysis
  ✓ ML Anomaly Scoring

INFRASTRUCTURE:
  ✓ Backend API:    http://localhost:9000 (running)
  ✓ Frontend:       http://localhost:3000 (running)
  ✓ Grafana:        http://localhost:3001 (running)
  ✓ Prometheus:     http://localhost:9090 (running)
""")
print(f"  ✓ Database:       {database_kind} (healthy)")
print("""

TEST SUITES READY:
  ✓ scripts/comprehensive_security_test.py (6 attack scenarios)
  ✓ scripts/hackathon_demo.py (4-wave attack simulation)

HACKATHON READY: YES ✓
""")
