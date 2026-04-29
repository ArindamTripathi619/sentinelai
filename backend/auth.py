from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from database import get_db
from models import User, Event, Alert, OtpSession
from scorer import score_registration, score_login, BehavioralPayload
from geo import get_country
from mailer import send_otp_email
import hashlib
import secrets
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# JWT imports
from jose import JWTError, jwt
from pydantic import BaseModel
from typing import Optional

load_dotenv()

router = APIRouter()

# JWT config
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    trust_score: int


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _get_registration_counts(db: Session, *, ip_address: str, user_agent: str, since: datetime) -> tuple[int, int]:
    registrations_from_ip = (
        db.query(Event)
        .filter(
            Event.action == "register",
            Event.ip_address == ip_address,
            Event.timestamp >= since,
        )
        .count()
    )
    same_ua_count = (
        db.query(Event)
        .filter(
            Event.action == "register",
            Event.user_agent == user_agent,
            Event.timestamp >= since,
        )
        .count()
    )
    return registrations_from_ip, same_ua_count


def _create_alerts(db: Session, user_id: str, email: str, triggered_rules: list[str]) -> None:
    severity_map = {
        "geo_drift": "high",
        "velocity_ip": "high",
        "speed_bot": "high",
        "duplicate_device": "medium",
        "email_pattern": "medium",
        "velocity_spike": "high",
        "platform_velocity_spike": "high",
    }
    for rule in triggered_rules:
        # Rename platform_velocity_spike to bot_wave for dashboard consistency
        alert_type = "bot_wave" if rule == "platform_velocity_spike" else rule
        db.add(
            Alert(
                type=alert_type,
                severity=severity_map.get(rule, "medium"),
                description=f"Rule triggered: {rule} for {email}",
                affected_user_ids=user_id,
            )
        )


def _extract_ip(request: Request, payload: dict) -> str:
    """
    Resolve the client IP with proxy/header support for local demo scripts.
    Priority: X-Forwarded-For header -> request payload -> socket client host.
    """
    xff = request.headers.get("x-forwarded-for")
    if xff:
        forwarded_ip = xff.split(",")[0].strip()
        if forwarded_ip:
            return forwarded_ip

    payload_ip = payload.get("ip_address")
    if payload_ip:
        return str(payload_ip)

    return request.client.host if request.client else "127.0.0.1"


def _extract_user_agent(request: Request, payload: dict) -> str:
    """Prefer real HTTP User-Agent header, then payload fallback for scripted tests."""
    return request.headers.get("user-agent") or payload.get("user_agent") or "unknown"


def create_access_token(user_id: str, expires_delta: timedelta = None) -> str:
    """Create a JWT access token for the user."""
    if expires_delta is None:
        expires_delta = timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    expire = datetime.utcnow() + expires_delta
    to_encode = {"sub": user_id, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    """
    Dependency to verify JWT token and get current user.
    Extracts token from Authorization header: "Bearer <token>"
    Used by all protected endpoints.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        # Extract token from "Bearer <token>" format
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authorization header format")
        
        token = parts[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

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
    beh_data = data.get("behavioralData") or data.get("behavioral") or {}
    behavioral = BehavioralPayload(
        typing_variance_ms=beh_data.get("typing_variance_ms", 150),
        time_to_complete_sec=beh_data.get("time_to_complete_sec", 10),
        mouse_move_count=beh_data.get("mouse_move_count", 20),
        keypress_count=beh_data.get("keypress_count", 20)
    )

    ip_address = _extract_ip(request, data)
    user_agent = _extract_user_agent(request, data)
    
    hour_ago = datetime.utcnow() - timedelta(hours=1)
    minute_ago = datetime.utcnow() - timedelta(minutes=1)
    reg_count, same_ua_count = _get_registration_counts(
        db,
        ip_address=ip_address,
        user_agent=user_agent,
        since=hour_ago,
    )
    
    # Query platform-wide registrations per minute for spike detection
    registrations_per_minute = (
        db.query(Event)
        .filter(Event.action == "register", Event.timestamp >= minute_ago)
        .count()
    )
    
    score_result = score_registration(
        email=email,
        behavioral=behavioral,
        ip_address=ip_address,
        user_agent=user_agent,
        registrations_from_ip_last_hour=reg_count,
        accounts_with_same_ua_today=same_ua_count,
        registrations_per_minute=registrations_per_minute,
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
    event = Event(
        user_id=new_user.id,
        action="register",
        ip_address=ip_address,
        country=get_country(ip_address),
        user_agent=user_agent,
        trust_score_at_time=score_result.trust_score,
        metadata_json=json.dumps({
            "triggered_rules": score_result.triggered_rules,
            "rule_penalty": score_result.rule_penalty,
            "behavioral_penalty": score_result.behavioral_penalty,
            "ml_penalty": score_result.ml_penalty,
            "ml_anomaly_score": score_result.ml_anomaly_score,
            "recommendation": score_result.recommendation,
        }),
    )
    db.add(event)
    
    # Create alerts if triggered
    _create_alerts(db, new_user.id, email, score_result.triggered_rules)
        
    db.commit()
    
    return {
        "message": "Registration successful",
        "trust_score": score_result.trust_score,
        "status": new_user.status,
        "triggered_rules": score_result.triggered_rules,
        "rule_penalty": score_result.rule_penalty,
        "behavioral_penalty": score_result.behavioral_penalty,
        "ml_penalty": score_result.ml_penalty,
        "recommendation": score_result.recommendation,
    }


@router.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")
    
    user = db.query(User).filter(User.email == email, User.password_hash == hash_password(password)).first()
    ip_address = _extract_ip(request, data)
    user_agent = _extract_user_agent(request, data)
    
    if not user:
        # log failed login maybe
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    current_country = get_country(ip_address)
    previous_login_event = (
        db.query(Event)
        .filter(Event.user_id == user.id, Event.action == "login")
        .order_by(Event.timestamp.desc())
        .first()
    )
    last_country = previous_login_event.country if previous_login_event else None
    minutes_since_last_login = None
    if previous_login_event and previous_login_event.timestamp:
        minutes_since_last_login = (
            (datetime.utcnow() - previous_login_event.timestamp).total_seconds() / 60.0
        )

    score_result = score_login(
        user_id=user.id,
        existing_trust_score=user.trust_score,
        ip_address=ip_address,
        current_country=current_country,
        last_country=last_country,
        minutes_since_last_login=minutes_since_last_login,
    )
    
    user.trust_score = score_result.trust_score
    user.status = "blocked" if score_result.trust_score < 20 else "quarantined" if score_result.trust_score < 40 else "active"
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    # Log event
    event = Event(
        user_id=user.id,
        action="login",
        ip_address=ip_address,
        country=current_country,
        user_agent=user_agent,
        trust_score_at_time=score_result.trust_score,
        metadata_json=json.dumps({
            "triggered_rules": score_result.triggered_rules,
            "rule_penalty": score_result.rule_penalty,
            "behavioral_penalty": score_result.behavioral_penalty,
            "ml_penalty": score_result.ml_penalty,
            "ml_anomaly_score": score_result.ml_anomaly_score,
            "recommendation": score_result.recommendation,
        }),
    )
    db.add(event)
    _create_alerts(db, user.id, email, score_result.triggered_rules)
    db.commit()
    
    # Generate JWT token
    access_token = create_access_token(user.id)
    
    # Determine action based on recommendation (progressive auth policy)
    # allow (>70): smooth login, otp (40-70): OTP challenge, captcha/quarantine (<40): block + alert
    otp_required = score_result.recommendation in ["otp", "captcha"]
    is_blocked = score_result.recommendation == "quarantine"
    
    if is_blocked:
        # Trust score too low — reject login and alert
        return {
            "token": None,
            "trust_score": score_result.trust_score,
            "otp_required": False,
            "is_blocked": True,
            "user_id": user.id,
            "recommendation": score_result.recommendation,
            "message": "Account flagged. Please contact support."
        }
    elif otp_required:
        # Create OTP session for medium-trust users
        otp_code = secrets.randbelow(1000000)
        otp_code_str = str(otp_code).zfill(6)
        otp_session = OtpSession(
            user_id=user.id,
            otp_code=otp_code_str,
            expires_at=datetime.utcnow() + timedelta(minutes=5)
        )
        db.add(otp_session)
        db.commit()
        db.refresh(otp_session)
        
        return {
            "token": None,
            "trust_score": score_result.trust_score,
            "otp_required": True,
            "otp_session_id": otp_session.id,
            "user_id": user.id,
            "recommendation": score_result.recommendation
        }
    else:
        # High-trust user — allow smooth login
        return {
            "token": access_token,
            "token_type": "bearer",
            "trust_score": score_result.trust_score,
            "otp_required": False,
            "user_id": user.id,
            "recommendation": score_result.recommendation
        }


@router.post("/otp/send")
async def send_otp(request: Request, db: Session = Depends(get_db)):
    """Send OTP code to user's email."""
    data = await request.json()
    otp_session_id = data.get("otp_session_id")
    email = data.get("email")
    
    if not otp_session_id or not email:
        raise HTTPException(status_code=400, detail="Missing otp_session_id or email")
    
    otp_session = db.query(OtpSession).filter(OtpSession.id == otp_session_id).first()
    
    if not otp_session:
        raise HTTPException(status_code=400, detail="Invalid OTP session")

    user = db.query(User).filter(User.id == otp_session.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")

    if user.email != email:
        raise HTTPException(status_code=400, detail="Email does not match OTP session")
    
    delivery_mode = send_otp_email(email, otp_session.otp_code)

    event = Event(
        user_id=user.id,
        action="otp_sent",
        ip_address=request.client.host if request.client else "127.0.0.1",
        user_agent=request.headers.get("user-agent", "unknown"),
        metadata_json=json.dumps({"otp_session_id": otp_session.id, "delivery_mode": delivery_mode}),
    )
    db.add(event)
    db.commit()
    
    expires_in_seconds = max(0, int((otp_session.expires_at - datetime.utcnow()).total_seconds()))
    return {
        "message": "OTP sent successfully",
        "expires_in_seconds": expires_in_seconds,
        "delivery_mode": delivery_mode,
    }


@router.post("/otp/verify")
async def verify_otp(request: Request, db: Session = Depends(get_db)):
    """Verify OTP code and issue JWT token."""
    data = await request.json()
    otp_session_id = data.get("otp_session_id")
    otp_code = data.get("otp_code")
    
    if not otp_session_id or not otp_code:
        raise HTTPException(status_code=400, detail="Missing otp_session_id or otp_code")
    
    otp_session = db.query(OtpSession).filter(OtpSession.id == otp_session_id).first()
    
    if not otp_session:
        raise HTTPException(status_code=400, detail="Invalid OTP session")
    
    if otp_session.used:
        raise HTTPException(status_code=400, detail="OTP already used")
    
    if datetime.utcnow() > otp_session.expires_at:
        raise HTTPException(status_code=400, detail="OTP expired")
    
    if otp_session.otp_code != otp_code:
        raise HTTPException(status_code=400, detail="Invalid OTP code")
    
    # Mark OTP as used
    otp_session.used = True
    db.commit()
    
    # Get user and generate JWT
    user = db.query(User).filter(User.id == otp_session.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    
    access_token = create_access_token(user.id)

    event = Event(
        user_id=user.id,
        action="otp_verified",
        ip_address=request.client.host if request.client else "127.0.0.1",
        user_agent=request.headers.get("user-agent", "unknown"),
        trust_score_at_time=user.trust_score,
        metadata_json=json.dumps({"otp_session_id": otp_session.id}),
    )
    db.add(event)
    db.commit()
    
    return {
        "token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "message": "Login successful"
    }
