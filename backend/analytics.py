from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from database import get_db
from models import User, Alert
from auth import get_current_user

router = APIRouter()

@router.get("/summary")
def get_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_users = db.query(User).count()
    
    today = datetime.utcnow().date()
    flagged_today = len([a for a in db.query(Alert).all() if a.timestamp.date() == today])
    bot_waves_detected = db.query(Alert).filter(Alert.type == "bot_wave").count()
    
    quarantined = db.query(User).filter(User.status == "quarantined").count()
    blocked = db.query(User).filter(User.status == "blocked").count()
    
    users = db.query(User).all()
    avg_trust_score = sum(u.trust_score for u in users) / len(users) if users else 0
    
    return {
        "total_users": total_users,
        "flagged_today": flagged_today,
        "bot_waves_detected": bot_waves_detected,
        "quarantined": quarantined,
        "blocked": blocked,
        "avg_trust_score": avg_trust_score
    }

@router.get("/velocity")
def velocity(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Basic velocity check for the last hour
    hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_users = db.query(User).filter(User.registered_at >= hour_ago).count()
    return {"window": "1h", "data": [{"time": str(hour_ago), "count": recent_users}], "spike_detected": recent_users > 50}

@router.get("/trust-distribution")
def trust_dist(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    users = db.query(User).all()
    bands = {"High": 0, "Medium": 0, "Low": 0}
    for u in users:
        if u.trust_score >= 70:
            bands["High"] += 1
        elif u.trust_score >= 40:
            bands["Medium"] += 1
        else:
            bands["Low"] += 1
    return {"bands": bands, "total": len(users)}
