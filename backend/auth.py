import os
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel
from typing import Optional
import random
import string

from database import get_db
from models import User, Event, OtpSession, Alert

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("JWT_SECRET", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

# Pydantic models
class RegisterRequest(BaseModel):
    email: str
    password: str
    typing_variance_ms: Optional[float] = None
    time_to_complete_sec: Optional[float] = None
    mouse_move_count: Optional[int] = None
    keypress_count: Optional[int] = None

class LoginRequest(BaseModel):
    email: str
    password: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class OtpSendRequest(BaseModel):
    email: str

class OtpVerifyRequest(BaseModel):
    email: str
    otp_code: str

@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == req.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(req.password)
    user = User(
        email=req.email,
        password_hash=hashed_password,
        typing_variance_ms=req.typing_variance_ms,
        time_to_complete_sec=req.time_to_complete_sec,
        mouse_move_count=req.mouse_move_count,
        keypress_count=req.keypress_count,
        trust_score=100
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    event = Event(
        user_id=user.id,
        action="register",
        trust_score_at_time=user.trust_score
    )
    db.add(event)
    db.commit()

    return {"message": "User registered successfully", "user_id": user.id}

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.password_hash):
        if user:
            event = Event(user_id=user.id, action="login_failed", ip_address=req.ip_address, user_agent=req.user_agent)
            db.add(event)
            db.commit()
        raise HTTPException(status_code=401, detail="Invalid credential")

    user.last_ip = req.ip_address
    user.last_login_at = datetime.utcnow()
    db.commit()

    event = Event(user_id=user.id, action="login", ip_address=req.ip_address, user_agent=req.user_agent, trust_score_at_time=user.trust_score)
    db.add(event)
    db.commit()

    # check trust score
    if user.trust_score < 40:
        return {"status": "otp_required"}

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.id}, expires_delta=access_token_expires)
    
    return {"access_token": access_token, "token_type": "bearer", "status": "success"}

def send_email_stub(to_email: str, subject: str, body: str):
    # Simulated SMTP send
    try:
        gmail_user = os.getenv("GMAIL_USER")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD")
        if gmail_user and gmail_password:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = gmail_user
            msg["To"] = to_email
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(gmail_user, gmail_password)
                server.sendmail(gmail_user, [to_email], msg.as_string())
        else:
            print(f"Mock SMTP to {to_email}: {subject} | {body}")
    except Exception as e:
        print(f"Failed to send email: {e}")

@router.post("/otp/send")
def send_otp(req: OtpSendRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    otp_code = ''.join(random.choices(string.digits, k=6))
    
    otp_session = OtpSession(
        user_id=user.id,
        otp_code=otp_code,
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db.add(otp_session)
    db.commit()

    send_email_stub(user.email, "SentinelAI OTP", f"Your OTP is {otp_code}")

    event = Event(user_id=user.id, action="otp_sent", trust_score_at_time=user.trust_score)
    db.add(event)
    db.commit()

    return {"message": "OTP sent"}

@router.post("/otp/verify")
def verify_otp(req: OtpVerifyRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    session = db.query(OtpSession).filter(
        OtpSession.user_id == user.id, 
        OtpSession.otp_code == req.otp_code,
        OtpSession.used == False,
        OtpSession.expires_at > datetime.utcnow()
    ).first()

    if not session:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    session.used = True
    db.commit()

    event = Event(user_id=user.id, action="otp_verified", trust_score_at_time=user.trust_score)
    db.add(event)
    db.commit()

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.id}, expires_delta=access_token_expires)
    
    return {"access_token": access_token, "token_type": "bearer", "status": "success"}
