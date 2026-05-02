from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
import json

from database import get_db
from models import Alert, User
from auth import get_current_user

router = APIRouter()

class ResolveAlertRequest(BaseModel):
    resolved: bool = True


def _parse_jsonish(value):
    if not value:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            return [item for item in value.split(",") if item]
    return []

@router.get("")
def get_alerts(
    limit: int = 20,
    severity: Optional[str] = None,
    since: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Alert)
    
    if severity:
        query = query.filter(Alert.severity == severity)
    if since:
        query = query.filter(Alert.timestamp >= since)
        
    alerts = query.order_by(Alert.timestamp.desc()).limit(limit).all()
    
    return {
        "alerts": [
            {
                "alert_id": a.id,
                "type": a.type,
                "severity": a.severity,
                "description": a.description,
                "affected_user_ids": _parse_jsonish(a.affected_user_ids),
                "timestamp": a.timestamp.isoformat() + "Z",
                "resolved": a.resolved
            }
            for a in alerts
        ]
    }

@router.patch("/{alert_id}/resolve")
def resolve_alert(
    alert_id: str, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    alert.resolved = True
    db.commit()
    
    return {
        "alert_id": alert.id,
        "resolved": alert.resolved
    }
