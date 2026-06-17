from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from database import get_db
from models import User, Alert, Event
from auth import get_current_user, require_admin

router = APIRouter()

@router.get("/summary")
def get_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), _admin: User = Depends(require_admin)):
    total_users = db.query(User).count()
    
    today = datetime.utcnow().date()
    # Filter alerts created today
    flagged_today = db.query(Alert).filter(Alert.timestamp >= today).count()
    bot_waves_detected = db.query(Alert).filter(Alert.type == "bot_wave", Alert.timestamp >= today).count()
    
    quarantined = db.query(User).filter(User.status == "quarantined").count()
    blocked = db.query(User).filter(User.status == "blocked").count()
    active_alerts = db.query(Alert).filter(Alert.resolved == False).count()
    
    users = db.query(User).all()
    avg_trust_score = sum(u.trust_score for u in users) / len(users) if users else 0
    
    return {
        "total_users": total_users,
        "flagged_today": flagged_today,
        "bot_waves_detected": bot_waves_detected,
        "quarantined": quarantined,
        "blocked": blocked,
        "active_alerts": active_alerts,
        "avg_trust_score": round(avg_trust_score, 1)
    }

def _parse_bucket_seconds(bucket: str) -> int:
    unit = bucket[-3:] if bucket.endswith("min") else bucket[-1:]
    val = int(bucket[:-3] if bucket.endswith("min") else bucket[:-1])
    if unit == "min":
        return val * 60
    elif unit == "h":
        return val * 3600
    return val

@router.get("/velocity")
def velocity(
    window: str = "1h",
    bucket: str = "1min",
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user),
    _admin: User = Depends(require_admin),
):
    now = datetime.utcnow()
    window_seconds = {"1h": 3600, "6h": 21600, "24h": 86400, "7d": 604800}.get(window, 3600)
    start_time = now - timedelta(seconds=window_seconds)
    bucket_seconds = _parse_bucket_seconds(bucket)

    regs = db.query(User.registered_at).filter(User.registered_at >= start_time).order_by(User.registered_at.asc()).all()

    buckets = {}
    bucket_count = (window_seconds + bucket_seconds - 1) // bucket_seconds
    for i in range(bucket_count):
        ts = start_time + timedelta(seconds=i * bucket_seconds)
        buckets[int(ts.timestamp())] = {"timestamp": ts.isoformat() + "Z", "registrations": 0}

    for (reg_ts,) in regs:
        bkey = int((reg_ts.timestamp() // bucket_seconds) * bucket_seconds)
        if bkey not in buckets:
            ts = datetime.fromtimestamp(bkey)
            buckets[bkey] = {"timestamp": ts.isoformat() + "Z", "registrations": 0}
        buckets[bkey]["registrations"] += 1

    data = sorted(buckets.values(), key=lambda x: x["timestamp"])
    spike_threshold = max(10, int(window_seconds / 60 * 0.5))
    spike_detected = any(d["registrations"] > spike_threshold for d in data)
    
    return {
        "window": window,
        "data": data,
        "spike_detected": spike_detected,
        "spike_at": max((d["timestamp"] for d in data if d["registrations"] > spike_threshold), default=None)
    }

@router.get("/trust-distribution")
def trust_dist(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), _admin: User = Depends(require_admin)):
    users = db.query(User).all()
    
    bands = [
        { "label": "Safe (80-100)",       "count": 0, "color": "green" },
        { "label": "Caution (60-79)",     "count": 0, "color": "yellow" },
        { "label": "Suspicious (40-59)", "count": 0, "color": "orange" },
        { "label": "Quarantined (20-39)","count": 0,  "color": "red" },
        { "label": "Blocked (0-19)",      "count": 0,  "color": "darkred" }
    ]
    
    for u in users:
        if u.trust_score >= 80: bands[0]["count"] += 1
        elif u.trust_score >= 60: bands[1]["count"] += 1
        elif u.trust_score >= 40: bands[2]["count"] += 1
        elif u.trust_score >= 20: bands[3]["count"] += 1
        else: bands[4]["count"] += 1
            
    return {
        "bands": bands,
        "total": len(users)
    }

