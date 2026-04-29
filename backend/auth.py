from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from database import get_db
from models import User, Event, Alert, OtpSession
from scorer import score_registration, score_login, BehavioralPayload
import hashlib
import secrets
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
    
    # Generate JWT token
    access_token = create_access_token(user.id)
    
    # Determine if OTP is needed
    otp_required = score_result.trust_score < 40
    
    if otp_required:
        # Create OTP session
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
            "user_id": user.id
        }
    else:
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
    
    # TODO: Implement actual email sending via Gmail SMTP
    # For now, just print to logs
    print(f"OTP for {email}: {otp_session.otp_code}")
    
    return {"message": "OTP sent successfully", "expires_in_seconds": 300}


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
    
    return {
        "token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "message": "Login successful"
    }
