from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models import User, Event, Alert
from scorer import score_registration, score_login, BehavioralPayload
import hashlib
from datetime import datetime

router = APIRouter()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

@router.post("/register")
async def register(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        raise HTTPException(status_code=400, detail="Missing email or password")
    
    # Check if user exists
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Parse behavioral payload
    beh_data = data.get("behavioralData", {})
    behavioral = BehavioralPayload(
        typing_variance_ms=beh_data.get("typing_variance_ms", 150),
        time_to_complete_sec=beh_data.get("time_to_complete_sec", 10),
        mouse_move_count=beh_data.get("mouse_move_count", 20),
        keypress_count=beh_data.get("keypress_count", 20)
    )
    
    ip_address = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Simple count for velocity check
    reg_count = db.query(User).filter(User.last_ip == ip_address).count()
    
    score_result = score_registration(
        email=email,
        behavioral=behavioral,
        ip_address=ip_address,
        user_agent=user_agent,
        registrations_from_ip_last_hour=reg_count,
        accounts_with_same_ua_today=reg_count
    )
    
    new_user = User(
        email=email,
        password_hash=hash_password(password),
        trust_score=score_result.trust_score,
        status="quarantined" if score_result.trust_score < 40 else "active",
        last_ip=ip_address,
        typing_variance_ms=behavioral.typing_variance_ms,
        time_to_complete_sec=behavioral.time_to_complete_sec,
        mouse_move_count=behavioral.mouse_move_count,
        keypress_count=behavioral.keypress_count,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Log event
    event = Event(user_id=new_user.id, action="register", ip_address=ip_address, user_agent=user_agent, trust_score_at_time=score_result.trust_score)
    db.add(event)
    
    # Create alerts if triggered
    for rule in score_result.triggered_rules:
        alert = Alert(type=rule, severity="medium" if score_result.trust_score > 40 else "high", description=f"Rule triggered: {rule} during registration of {email}", affected_user_ids=new_user.id)
        db.add(alert)
        
    db.commit()
    
    return {"message": "Registration successful", "trust_score": score_result.trust_score, "status": new_user.status}


@router.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")
    
    user = db.query(User).filter(User.email == email, User.password_hash == hash_password(password)).first()
    ip_address = request.client.host if request.client else "127.0.0.1"
    
    if not user:
        # log failed login maybe
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    score_result = score_login(
        user_id=user.id,
        existing_trust_score=user.trust_score,
        ip_address=ip_address,
        current_country="IN", # Mock
        last_country="IN", # Mock
        minutes_since_last_login=100
    )
    
    user.trust_score = score_result.trust_score
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    # Log event
    event = Event(user_id=user.id, action="login", ip_address=ip_address, trust_score_at_time=score_result.trust_score)
    db.add(event)
    db.commit()
    
    return {"message": "Login successful", "trust_score": score_result.trust_score, "recommendation": score_result.recommendation}

@router.get("/users")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return {"users": [{"id": u.id, "email": u.email, "score": u.trust_score, "status": u.status, "ip": u.last_ip} for u in users]}

@router.get("/alerts")
def get_alerts(db: Session = Depends(get_db)):
    alerts = db.query(Alert).order_by(Alert.timestamp.desc()).limit(20).all()
    return {"alerts": [{"id": a.id, "type": a.type, "severity": a.severity, "desc": a.description, "time": str(a.timestamp)} for a in alerts]}
