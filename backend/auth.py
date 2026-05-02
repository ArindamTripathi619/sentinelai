from datetime import datetime, timedelta
import json
import os
from typing import Any, Optional, cast

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from database import get_db
from geo import get_country
from models import Alert, Event, User
from scorer import BehavioralPayload, score_login, score_registration

load_dotenv()

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

SUPABASE_URL = os.getenv("SUPABASE_URL", os.getenv("VITE_SUPABASE_URL", "")).rstrip("/")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", os.getenv("VITE_SUPABASE_ANON_KEY", ""))
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_API_KEY = SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    trust_score: int


class CaptchaVerifyRequest(BaseModel):
    captcha_token: str
    captcha_answer: str


class CaptchaChallengeResponse(BaseModel):
    captcha_required: bool
    captcha_token: str
    captcha_prompt: str
    user_id: str
    recommendation: str


class TrustSyncRequest(BaseModel):
    event_type: str = "login"
    behavioral: dict = {}
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    country: Optional[str] = None


def _auth_headers(access_token: Optional[str] = None) -> dict:
    if not SUPABASE_URL or not SUPABASE_API_KEY:
        raise HTTPException(status_code=500, detail="Supabase is not configured")

    headers = {
        "apikey": SUPABASE_API_KEY,
        "Content-Type": "application/json",
    }
    headers["Authorization"] = f"Bearer {access_token or SUPABASE_API_KEY}"
    return headers


async def _supabase_request(
    method: str,
    path: str,
    *,
    json_body: Optional[dict] = None,
    access_token: Optional[str] = None,
) -> dict:
    url = f"{SUPABASE_URL}{path}"
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.request(method, url, headers=_auth_headers(access_token), json=json_body)

    if response.status_code >= 400:
        try:
            detail = response.json()
        except Exception:
            detail = {"error": response.text}
        raise HTTPException(
            status_code=response.status_code,
            detail=detail.get("msg") or detail.get("error_description") or detail.get("error") or detail,
        )

    if response.content:
        return response.json()
    return {}


async def _supabase_signup(email: str, password: str, user_data: Optional[dict] = None) -> dict:
    payload: dict[str, object] = {"email": email, "password": password}
    if user_data:
        payload["data"] = user_data
    return await _supabase_request("POST", "/auth/v1/signup", json_body=payload)


async def _supabase_signin(email: str, password: str) -> dict:
    return await _supabase_request(
        "POST",
        "/auth/v1/token?grant_type=password",
        json_body={"email": email, "password": password},
    )


async def _supabase_get_user(access_token: str) -> dict:
    return await _supabase_request("GET", "/auth/v1/user", access_token=access_token)


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


def _parse_metadata(value):
    if not value:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


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
        alert_type = "bot_wave" if rule == "platform_velocity_spike" else rule
        db.add(
            Alert(
                type=alert_type,
                severity=severity_map.get(rule, "medium"),
                description=f"Rule triggered: {rule} for {email}",
                affected_user_ids=[user_id],
            )
        )


def _create_ml_alert(db: Session, user_id: str, email: str, ml_anomaly_score: Optional[float]) -> None:
    if ml_anomaly_score is None or ml_anomaly_score > -0.5:
        return

    severity = "high" if ml_anomaly_score <= -0.8 else "medium"
    db.add(
        Alert(
            type="ml_anomaly",
            severity=severity,
            description=f"ML anomaly detected for {email} (score: {ml_anomaly_score:.2f})",
            affected_user_ids=[user_id],
        )
    )


def _extract_ip(request: Request, payload: dict) -> str:
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
    return request.headers.get("user-agent") or payload.get("user_agent") or "unknown"


def _ensure_user_row(
    db: Session,
    *,
    user_id: str,
    email: str,
    trust_score: int = 100,
    status: str = "active",
    last_ip: Optional[str] = None,
    behavioral: Optional[BehavioralPayload] = None,
    ml_anomaly_score: Optional[float] = None,
    triggered_flags: Optional[list[str]] = None,
) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, email=email, trust_score=trust_score, status=status)
        db.add(user)

    user_obj = cast(Any, user)

    user_obj.email = email or user_obj.email
    user_obj.trust_score = trust_score
    user_obj.status = status
    user_obj.last_ip = last_ip or user_obj.last_ip
    if behavioral:
        user_obj.typing_variance_ms = behavioral.typing_variance_ms
        user_obj.time_to_complete_sec = behavioral.time_to_complete_sec
        user_obj.mouse_move_count = behavioral.mouse_move_count
        user_obj.keypress_count = behavioral.keypress_count
    if ml_anomaly_score is not None:
        user_obj.ml_anomaly_score = ml_anomaly_score
    if triggered_flags is not None:
        user_obj.triggered_flags = triggered_flags
    return user_obj


def _behavioral_payload_from_dict(data: dict) -> BehavioralPayload:
    return BehavioralPayload(
        typing_variance_ms=float(data.get("typing_variance_ms", 150)),
        time_to_complete_sec=float(data.get("time_to_complete_sec", 10)),
        mouse_move_count=int(data.get("mouse_move_count", 20)),
        keypress_count=int(data.get("keypress_count", 20)),
        session_tempo_sec=float(data.get("session_tempo_sec", 0.0)),
        mouse_entropy_score=float(data.get("mouse_entropy_score", 0.0)),
        fill_order_score=float(data.get("fill_order_score", 1.0)),
    )


async def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    access_token = parts[1]
    try:
        auth_user = await _supabase_get_user(access_token)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(User).filter(User.id == auth_user["id"]).first()
    if not user:
        user = _ensure_user_row(db, user_id=auth_user["id"], email=auth_user.get("email") or "")
        db.commit()
        db.refresh(user)

    return user


@limiter.limit("5/minute")
@router.post("/register")
async def register(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        raise HTTPException(status_code=400, detail="Missing email or password")

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Registration failed. Please try again or contact support.")

    beh_data = data.get("behavioralData") or data.get("behavioral") or {}
    behavioral = BehavioralPayload(
        typing_variance_ms=float(beh_data.get("typing_variance_ms", 150)),
        time_to_complete_sec=float(beh_data.get("time_to_complete_sec", 10)),
        mouse_move_count=int(beh_data.get("mouse_move_count", 20)),
        keypress_count=int(beh_data.get("keypress_count", 20)),
        session_tempo_sec=float(beh_data.get("session_tempo_sec", 0.0)),
        mouse_entropy_score=float(beh_data.get("mouse_entropy_score", 0.0)),
        fill_order_score=float(beh_data.get("fill_order_score", 1.0)),
    )

    ip_address = _extract_ip(request, data)
    user_agent = _extract_user_agent(request, data)
    hour_ago = datetime.utcnow() - timedelta(hours=1)
    minute_ago = datetime.utcnow() - timedelta(minutes=1)
    reg_count, same_ua_count = _get_registration_counts(db, ip_address=ip_address, user_agent=user_agent, since=hour_ago)
    registrations_per_minute = db.query(Event).filter(Event.action == "register", Event.timestamp >= minute_ago).count()

    auth_response = await _supabase_signup(email, password, user_data={"full_name": data.get("name")})
    supabase_user = auth_response.get("user") or {}
    if not supabase_user.get("id"):
        raise HTTPException(status_code=400, detail="Supabase registration failed")

    score_result = score_registration(
        email=email,
        behavioral=behavioral,
        ip_address=ip_address,
        user_agent=user_agent,
        registrations_from_ip_last_hour=reg_count,
        accounts_with_same_ua_today=same_ua_count,
        ml_anomaly_score=None,
        registrations_per_minute=registrations_per_minute,
    )

    new_user = _ensure_user_row(
        db,
        user_id=supabase_user["id"],
        email=supabase_user.get("email") or email,
        trust_score=score_result.trust_score,
        status="quarantined" if score_result.trust_score < 40 else "active",
        last_ip=ip_address,
        behavioral=behavioral,
        ml_anomaly_score=score_result.ml_anomaly_score,
        triggered_flags=score_result.triggered_rules,
    )
    new_user_obj = cast(Any, new_user)

    db.add(
        Event(
            user_id=str(new_user_obj.id),
            action="register",
            ip_address=ip_address,
            country=get_country(ip_address),
            user_agent=user_agent,
            trust_score_at_time=score_result.trust_score,
            metadata_json={
                "triggered_rules": score_result.triggered_rules,
                "rule_penalty": score_result.rule_penalty,
                "behavioral_penalty": score_result.behavioral_penalty,
                "ml_penalty": score_result.ml_penalty,
                "ml_anomaly_score": score_result.ml_anomaly_score,
                "recommendation": score_result.recommendation,
            },
        )
    )
    _create_alerts(db, str(new_user_obj.id), email, score_result.triggered_rules)
    _create_ml_alert(db, str(new_user_obj.id), email, score_result.ml_anomaly_score)
    db.commit()
    db.refresh(new_user)

    session = auth_response.get("session") or {}
    return {
        "message": "Registration successful",
        "user_id": str(new_user_obj.id),
        "trust_score": score_result.trust_score,
        "status": new_user_obj.status,
        "triggered_rules": score_result.triggered_rules,
        "rule_penalty": score_result.rule_penalty,
        "behavioral_penalty": score_result.behavioral_penalty,
        "ml_penalty": score_result.ml_penalty,
        "recommendation": score_result.recommendation,
        "token": session.get("access_token"),
        "token_type": session.get("token_type", "bearer"),
    }


@limiter.limit("10/minute")
@router.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Missing email or password")

    auth_response = await _supabase_signin(email, password)
    session = auth_response.get("session") or {}
    auth_user = auth_response.get("user") or {}
    if not auth_user.get("id") or not session.get("access_token"):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    ip_address = _extract_ip(request, data)
    user_agent = _extract_user_agent(request, data)
    current_country = get_country(ip_address)

    user = db.query(User).filter(User.id == auth_user["id"]).first()
    if not user:
        user = _ensure_user_row(db, user_id=auth_user["id"], email=auth_user.get("email") or email)
        db.commit()
        db.refresh(user)

    user_obj = cast(Any, user)

    previous_login_event = (
        db.query(Event)
        .filter(Event.user_id == user.id, Event.action == "login")
        .order_by(Event.timestamp.desc())
        .first()
    )
    last_country: Optional[str] = None
    if previous_login_event is not None:
        last_country = cast(Optional[str], previous_login_event.country)
    minutes_since_last_login = None
    if previous_login_event is not None and previous_login_event.timestamp is not None:
        minutes_since_last_login = (datetime.utcnow() - previous_login_event.timestamp).total_seconds() / 60.0

    score_result = score_login(
        user_id=str(user_obj.id),
        existing_trust_score=int(user_obj.trust_score),
        ip_address=ip_address,
        current_country=current_country,
        last_country=last_country,
        minutes_since_last_login=minutes_since_last_login,
    )

    user_obj.trust_score = score_result.trust_score
    user_obj.status = "blocked" if score_result.trust_score < 20 else "quarantined" if score_result.trust_score < 40 else "active"
    user_obj.last_login_at = datetime.utcnow()
    user_obj.last_ip = ip_address

    db.add(
        Event(
            user_id=str(user_obj.id),
            action="login",
            ip_address=ip_address,
            country=current_country,
            user_agent=user_agent,
            trust_score_at_time=score_result.trust_score,
            metadata_json={
                "rule_penalty": score_result.rule_penalty,
                "behavioral_penalty": score_result.behavioral_penalty,
                "ml_penalty": score_result.ml_penalty,
                "ml_anomaly_score": score_result.ml_anomaly_score,
                "recommendation": score_result.recommendation,
            },
        )
    )
    _create_alerts(db, str(user_obj.id), email, score_result.triggered_rules)
    _create_ml_alert(db, str(user_obj.id), email, score_result.ml_anomaly_score)
    db.commit()

    if score_result.trust_score < 20:
        return {
            "token": None,
            "trust_score": score_result.trust_score,
            "otp_required": False,
            "captcha_required": False,
            "is_blocked": True,
            "user_id": str(user_obj.id),
            "recommendation": score_result.recommendation,
            "message": "Account flagged. Please contact support.",
        }

    return {
        "token": session.get("access_token"),
        "token_type": session.get("token_type", "bearer"),
        "trust_score": score_result.trust_score,
        "otp_required": False,
        "captcha_required": False,
        "is_blocked": False,
        "user_id": str(user_obj.id),
        "recommendation": score_result.recommendation,
    }


@router.post("/captcha/verify")
async def verify_captcha(_: Request, __: Session = Depends(get_db)):
    raise HTTPException(status_code=410, detail="Captcha flow is handled by Supabase Auth now")


@router.post("/otp/send")
async def send_otp(_: Request, __: Session = Depends(get_db)):
    raise HTTPException(status_code=410, detail="OTP flow is handled by Supabase Auth now")


@router.post("/otp/verify")
async def verify_otp(_: Request, __: Session = Depends(get_db)):
    raise HTTPException(status_code=410, detail="OTP flow is handled by Supabase Auth now")


@router.post("/sync")
async def sync_trust(request: Request, payload: TrustSyncRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    data = payload.behavioral or {}
    behavioral = _behavioral_payload_from_dict(data)
    ip_address = payload.ip_address or _extract_ip(request, {"ip_address": payload.ip_address} if payload.ip_address else {})
    user_agent = payload.user_agent or _extract_user_agent(request, {"user_agent": payload.user_agent} if payload.user_agent else {})
    current_user_obj = cast(Any, current_user)
    email = str(current_user_obj.email)

    if payload.event_type == "register":
        hour_ago = datetime.utcnow() - timedelta(hours=1)
        minute_ago = datetime.utcnow() - timedelta(minutes=1)
        reg_count, same_ua_count = _get_registration_counts(db, ip_address=ip_address, user_agent=user_agent, since=hour_ago)
        registrations_per_minute = db.query(Event).filter(Event.action == "register", Event.timestamp >= minute_ago).count()

        score_result = score_registration(
            email=email,
            behavioral=behavioral,
            ip_address=ip_address,
            user_agent=user_agent,
            registrations_from_ip_last_hour=reg_count,
            accounts_with_same_ua_today=same_ua_count,
            ml_anomaly_score=None,
            registrations_per_minute=registrations_per_minute,
        )

        user = _ensure_user_row(
            db,
            user_id=str(current_user_obj.id),
            email=email,
            trust_score=score_result.trust_score,
            status="quarantined" if score_result.trust_score < 40 else "active",
            last_ip=ip_address,
            behavioral=behavioral,
            ml_anomaly_score=score_result.ml_anomaly_score,
            triggered_flags=score_result.triggered_rules,
        )
        user_obj = cast(Any, user)
        db.add(
            Event(
                user_id=str(user_obj.id),
                action="register",
                ip_address=ip_address,
                country=payload.country or get_country(ip_address),
                user_agent=user_agent,
                trust_score_at_time=score_result.trust_score,
                metadata_json={
                    "triggered_rules": score_result.triggered_rules,
                    "rule_penalty": score_result.rule_penalty,
                    "behavioral_penalty": score_result.behavioral_penalty,
                    "ml_penalty": score_result.ml_penalty,
                    "ml_anomaly_score": score_result.ml_anomaly_score,
                    "recommendation": score_result.recommendation,
                },
            )
        )
        _create_alerts(db, str(user_obj.id), email, score_result.triggered_rules)
        _create_ml_alert(db, str(user_obj.id), email, score_result.ml_anomaly_score)
        db.commit()
        db.refresh(user)
        return {
            "user_id": str(user_obj.id),
            "trust_score": score_result.trust_score,
            "status": user_obj.status,
            "recommendation": score_result.recommendation,
        }

    previous_login_event = (
        db.query(Event)
        .filter(Event.user_id == str(current_user_obj.id), Event.action == "login")
        .order_by(Event.timestamp.desc())
        .first()
    )
    last_country: Optional[str] = None
    if previous_login_event is not None:
        last_country = cast(Optional[str], previous_login_event.country)

    minutes_since_last_login = None
    if previous_login_event is not None and previous_login_event.timestamp is not None:
        minutes_since_last_login = (datetime.utcnow() - previous_login_event.timestamp).total_seconds() / 60.0

    score_result = score_login(
        user_id=str(current_user_obj.id),
        existing_trust_score=int(current_user_obj.trust_score),
        ip_address=ip_address,
        current_country=payload.country or get_country(ip_address),
        last_country=last_country,
        minutes_since_last_login=minutes_since_last_login,
    )

    current_user_obj.trust_score = score_result.trust_score
    current_user_obj.status = "blocked" if score_result.trust_score < 20 else "quarantined" if score_result.trust_score < 40 else "active"
    current_user_obj.last_login_at = datetime.utcnow()
    current_user_obj.last_ip = ip_address
    current_user_obj.typing_variance_ms = behavioral.typing_variance_ms
    current_user_obj.time_to_complete_sec = behavioral.time_to_complete_sec
    current_user_obj.mouse_move_count = behavioral.mouse_move_count
    current_user_obj.keypress_count = behavioral.keypress_count
    current_user_obj.ml_anomaly_score = score_result.ml_anomaly_score
    current_user_obj.triggered_flags = score_result.triggered_rules

    db.add(
        Event(
            user_id=str(current_user_obj.id),
            action="login",
            ip_address=ip_address,
            country=payload.country or get_country(ip_address),
            user_agent=user_agent,
            trust_score_at_time=score_result.trust_score,
            metadata_json={
                "rule_penalty": score_result.rule_penalty,
                "behavioral_penalty": score_result.behavioral_penalty,
                "ml_penalty": score_result.ml_penalty,
                "ml_anomaly_score": score_result.ml_anomaly_score,
                "recommendation": score_result.recommendation,
            },
        )
    )
    _create_alerts(db, str(current_user_obj.id), email, score_result.triggered_rules)
    _create_ml_alert(db, str(current_user_obj.id), email, score_result.ml_anomaly_score)
    db.commit()

    return {
        "user_id": str(current_user_obj.id),
        "trust_score": score_result.trust_score,
        "status": current_user_obj.status,
        "recommendation": score_result.recommendation,
    }
