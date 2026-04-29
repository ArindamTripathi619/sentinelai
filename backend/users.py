from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import User, Event

router = APIRouter()

@router.get("")
def get_users(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    users = db.query(User).offset(skip).limit(limit).all()
    return {
        "total": db.query(User).count(),
        "users": [
            {
                "id": u.id,
                "email": u.email,
                "trust_score": u.trust_score,
                "status": u.status,
                "registered_at": u.registered_at,
                "last_ip": u.last_ip,
                "is_admin": u.is_admin
            }
            for u in users
        ]
    }

@router.get("/{user_id}/timeline")
def get_user_timeline(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    events = db.query(Event).filter(Event.user_id == user_id).order_by(Event.timestamp.desc()).all()
    
    return {
        "user_id": user_id,
        "timeline": [
            {
                "id": e.id,
                "action": e.action,
                "ip_address": e.ip_address,
                "user_agent": e.user_agent,
                "trust_score_at_time": e.trust_score_at_time,
                "timestamp": e.timestamp
            }
            for e in events
        ]
    }
