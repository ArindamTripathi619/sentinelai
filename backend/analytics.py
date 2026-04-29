from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from models import User, Alert

router = APIRouter()

@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
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
def velocity_stub():
    return {"window": "1h", "data": [], "spike_detected": False}

@router.get("/trust-distribution")
def trust_dist_stub():
    return {"bands": [], "total": 0}
