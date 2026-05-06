from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Literal
from pydantic import BaseModel

from database import get_db
from models import User
from auth import get_current_user
from scorer import BehavioralPayload, score_login, score_registration

# Try to import ML model, but make it optional for Render deployment
_ML_AVAILABLE = False
try:
    from ml_model import build_feature_vector, predict, get_model
    _ML_AVAILABLE = True
except ImportError:
    # ML dependencies not available in this deployment target
    pass

router = APIRouter()
def _ml_score_fallback() -> float:
    """Fallback ML score when sklearn/numpy are not available."""
    return 0.5



class ScoringRequest(BaseModel):
    user_id: str
    behavioral: dict
    ip_address: str
    email: str
    user_agent: str
    registrations_from_ip_last_hour: int
    accounts_with_same_ua_today: int = 0
    event_type: Literal["register", "login"] = "register"
    current_country: Optional[str] = None
    last_country: Optional[str] = None
    minutes_since_last_login: Optional[float] = None
    registrations_per_minute: int = 0


def _behavioral_payload(data: dict) -> BehavioralPayload:
    return BehavioralPayload(
        typing_variance_ms=float(data.get("typing_variance_ms", 150)),
        time_to_complete_sec=float(data.get("time_to_complete_sec", 10)),
        mouse_move_count=int(data.get("mouse_move_count", 20)),
        keypress_count=int(data.get("keypress_count", 20)),
    )


def _ml_score(req: ScoringRequest) -> float:
    if not _ML_AVAILABLE:
        return _ml_score_fallback()
    
    behavioral = req.behavioral or {}
    feature_vector = build_feature_vector(
        float(behavioral.get("typing_variance_ms", 150)),
        float(behavioral.get("time_to_complete_sec", 10)),
        int(behavioral.get("mouse_move_count", 20)),
        int(req.registrations_from_ip_last_hour),
        0.1 if "temp" in req.email.lower() or "mail" in req.email.lower() else 0.95,
        int(behavioral.get("keypress_count", 20)),
        float(behavioral.get("session_actions_per_min", 4)),
    )
    return predict(feature_vector, get_model())


@router.post("")
def calculate_score(
    req: ScoringRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    behavioral = _behavioral_payload(req.behavioral)
    ml_anomaly_score = _ml_score(req)

    if req.event_type == "login":
        user = db.query(User).filter(User.id == req.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        result = score_login(
            user_id=req.user_id,
            existing_trust_score=user.trust_score,
            ip_address=req.ip_address,
            current_country=req.current_country or "Unknown",
            last_country=req.last_country,
            minutes_since_last_login=req.minutes_since_last_login,
            ml_anomaly_score=ml_anomaly_score,
        )
    else:
        result = score_registration(
            email=req.email,
            behavioral=behavioral,
            ip_address=req.ip_address,
            user_agent=req.user_agent,
            registrations_from_ip_last_hour=req.registrations_from_ip_last_hour,
            accounts_with_same_ua_today=req.accounts_with_same_ua_today,
            ml_anomaly_score=ml_anomaly_score,
            registrations_per_minute=req.registrations_per_minute,
        )

    return {
        "trust_score": result.trust_score,
        "ml_anomaly_score": result.ml_anomaly_score,
        "rule_penalty": result.rule_penalty,
        "behavioral_penalty": result.behavioral_penalty,
        "ml_penalty": result.ml_penalty,
        "triggered_rules": result.triggered_rules,
        "recommendation": result.recommendation,
        "event_type": req.event_type,
    }
