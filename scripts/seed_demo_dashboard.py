#!/usr/bin/env python3
"""Seed SentinelAI with deterministic demo users, alerts, and timelines.

This script is rerunnable. It replaces the demo rows it owns and repopulates
users across the full trust-score spectrum so the dashboard has meaningful data.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

import bcrypt
from dotenv import load_dotenv
from sqlalchemy import or_

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Load the single project `.env` from the repository root. Keep a single canonical `.env`.
load_dotenv(ROOT / ".env", override=False)

from database import build_engine  # noqa: E402
from models import Alert, Event, OtpSession, User, Base  # noqa: E402


DEMO_PASSWORD = "DemoPass!234"
ADMIN_EMAIL = "admin.demo@sentinelai.local"
DEMO_SEED_TAG = "Demo seed:"


@dataclass(frozen=True)
class DemoProfile:
    email: str
    trust_score: int
    status: str
    last_ip: str
    country: str
    recommendation: str
    triggered_rules: list[str]
    otp_mode: str | None = None
    is_admin: bool = False


DEMO_USERS: list[DemoProfile] = [
    DemoProfile(
        email=ADMIN_EMAIL,
        trust_score=98,
        status="active",
        last_ip="103.21.58.12",
        country="India",
        recommendation="direct",
        triggered_rules=[],
        is_admin=True,
    ),
    DemoProfile(
        email="ananya.sharma@sentinelai.local",
        trust_score=91,
        status="active",
        last_ip="106.51.71.200",
        country="India",
        recommendation="direct",
        triggered_rules=[],
    ),
    DemoProfile(
        email="rahul.verma@sentinelai.local",
        trust_score=86,
        status="active",
        last_ip="122.177.94.21",
        country="India",
        recommendation="direct",
        triggered_rules=[],
    ),
    DemoProfile(
        email="meera.patel@sentinelai.local",
        trust_score=76,
        status="active",
        last_ip="49.36.80.45",
        country="India",
        recommendation="direct",
        triggered_rules=[],
    ),
    DemoProfile(
        email="ishaan.rao@sentinelai.local",
        trust_score=68,
        status="active",
        last_ip="103.245.96.22",
        country="India",
        recommendation="otp",
        triggered_rules=["email_pattern"],
        otp_mode="otp",
    ),
    DemoProfile(
        email="pooja.ghosh@sentinelai.local",
        trust_score=61,
        status="active",
        last_ip="115.240.98.1",
        country="India",
        recommendation="otp",
        triggered_rules=["geo_drift"],
        otp_mode="otp",
    ),
    DemoProfile(
        email="amit.bose@sentinelai.local",
        trust_score=57,
        status="active",
        last_ip="59.144.68.200",
        country="India",
        recommendation="captcha",
        triggered_rules=["speed_bot"],
        otp_mode="captcha",
    ),
    DemoProfile(
        email="tanvi.khan@sentinelai.local",
        trust_score=43,
        status="active",
        last_ip="182.73.100.3",
        country="India",
        recommendation="captcha",
        triggered_rules=["duplicate_device"],
        otp_mode="captcha",
    ),
    DemoProfile(
        email="rhea.das@sentinelai.local",
        trust_score=38,
        status="quarantined",
        last_ip="27.7.90.1",
        country="India",
        recommendation="quarantine",
        triggered_rules=["geo_drift", "email_pattern"],
    ),
    DemoProfile(
        email="kabir.mehta@sentinelai.local",
        trust_score=27,
        status="quarantined",
        last_ip="117.200.45.80",
        country="India",
        recommendation="quarantine",
        triggered_rules=["speed_bot", "bot_wave"],
    ),
    DemoProfile(
        email="divya.iyer@sentinelai.local",
        trust_score=16,
        status="blocked",
        last_ip="45.118.144.200",
        country="India",
        recommendation="blocked",
        triggered_rules=["bot_wave", "duplicate_device"],
    ),
    DemoProfile(
        email="nikhil.joshi@sentinelai.local",
        trust_score=8,
        status="blocked",
        last_ip="14.142.107.112",
        country="India",
        recommendation="blocked",
        triggered_rules=["bot_wave", "velocity_spike"],
    ),
]


ALERT_SEEDS = [
    {
        "type": "bot_wave",
        "severity": "high",
        "description": "Demo seed: bot wave detected across a burst of suspicious registrations.",
        "affected": ["divya.iyer@sentinelai.local", "nikhil.joshi@sentinelai.local", "kabir.mehta@sentinelai.local"],
        "minutes_ago": 12,
    },
    {
        "type": "geo_drift",
        "severity": "medium",
        "description": "Demo seed: geo drift mismatch detected for a repeated campus login.",
        "affected": ["pooja.ghosh@sentinelai.local", "rhea.das@sentinelai.local"],
        "minutes_ago": 25,
    },
    {
        "type": "speed_bot",
        "severity": "high",
        "description": "Demo seed: unusually fast form completion pattern observed.",
        "affected": ["amit.bose@sentinelai.local", "kabir.mehta@sentinelai.local"],
        "minutes_ago": 40,
    },
    {
        "type": "duplicate_device",
        "severity": "medium",
        "description": "Demo seed: repeated device fingerprint seen across multiple accounts.",
        "affected": ["tanvi.khan@sentinelai.local", "divya.iyer@sentinelai.local"],
        "minutes_ago": 55,
    },
    {
        "type": "email_pattern",
        "severity": "low",
        "description": "Demo seed: sequential email naming pattern flagged for review.",
        "affected": ["ishaan.rao@sentinelai.local", "pooja.ghosh@sentinelai.local"],
        "minutes_ago": 70,
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed SentinelAI with demo trust-level data.")
    parser.add_argument(
        "--db-url",
        default=os.getenv("DATABASE_URL", "sqlite:///./sentinel.db"),
        help="Database URL. Defaults to DATABASE_URL or the local SQLite DB.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        default=True,
        help="Replace existing demo rows before seeding (default: on).",
    )
    parser.add_argument(
        "--no-reset",
        action="store_false",
        dest="reset",
        help="Keep existing demo rows and skip replacement.",
    )
    return parser.parse_args()


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def utc_now_naive() -> datetime:
    return datetime.utcnow().replace(microsecond=0)


def demo_metadata(profile: DemoProfile, *, recommendation: str) -> str:
    return json.dumps(
        {
            "demo_seed": True,
            "trust_score": profile.trust_score,
            "status": profile.status,
            "triggered_rules": profile.triggered_rules,
            "recommendation": recommendation,
        }
    )


def register_event_metadata(profile: DemoProfile) -> str:
    return json.dumps(
        {
            "demo_seed": True,
            "triggered_rules": profile.triggered_rules,
            "recommendation": profile.recommendation,
            "trust_score": profile.trust_score,
        }
    )


def delete_demo_rows(session) -> None:
    demo_emails = [profile.email for profile in DEMO_USERS]
    existing_users = session.query(User).filter(User.email.in_(demo_emails)).all()
    existing_ids = [user.id for user in existing_users]

    if existing_ids:
        session.query(Event).filter(Event.user_id.in_(existing_ids)).delete(synchronize_session=False)
        session.query(OtpSession).filter(OtpSession.user_id.in_(existing_ids)).delete(synchronize_session=False)

    session.query(Alert).filter(Alert.description.like(f"{DEMO_SEED_TAG}%")).delete(synchronize_session=False)
    session.query(User).filter(User.email.in_(demo_emails)).delete(synchronize_session=False)
    session.commit()


def seed_users(session) -> dict[str, str]:
    base_time = utc_now_naive() - timedelta(hours=6)
    seeded_ids: dict[str, str] = {}

    for index, profile in enumerate(DEMO_USERS):
        registered_at = base_time + timedelta(minutes=index * 22)
        user = User(
            email=profile.email,
            password_hash=hash_password(DEMO_PASSWORD),
            trust_score=profile.trust_score,
            status=profile.status,
            registered_at=registered_at,
            last_login_at=registered_at + timedelta(minutes=8) if profile.status == "active" else None,
            last_ip=profile.last_ip,
            is_admin=profile.is_admin,
            typing_variance_ms=max(25.0, round(210 - (profile.trust_score * 1.2), 1)),
            time_to_complete_sec=max(5.0, round(16 - (profile.trust_score / 12), 1)),
            mouse_move_count=max(5, 160 - profile.trust_score),
            keypress_count=max(12, 180 - profile.trust_score),
            ml_anomaly_score=round(max(0.02, (100 - profile.trust_score) / 100), 3),
            triggered_flags=json.dumps(profile.triggered_rules),
        )
        session.add(user)
        session.flush()
        seeded_ids[profile.email] = user.id

        session.add(
            Event(
                user_id=user.id,
                action="register",
                ip_address=profile.last_ip,
                country=profile.country,
                user_agent="SentinelAI Demo Seeder/1.0",
                trust_score_at_time=profile.trust_score,
                timestamp=registered_at,
                metadata_json=register_event_metadata(profile),
            )
        )

        if profile.status == "active":
            session.add(
                Event(
                    user_id=user.id,
                    action="login",
                    ip_address=profile.last_ip,
                    country=profile.country,
                    user_agent="SentinelAI Demo Seeder/1.0",
                    trust_score_at_time=profile.trust_score,
                    timestamp=registered_at + timedelta(minutes=10),
                    metadata_json=demo_metadata(profile, recommendation=profile.recommendation),
                )
            )
        elif profile.status == "quarantined":
            session.add(
                Event(
                    user_id=user.id,
                    action="quarantined",
                    ip_address=profile.last_ip,
                    country=profile.country,
                    user_agent="SentinelAI Demo Seeder/1.0",
                    trust_score_at_time=profile.trust_score,
                    timestamp=registered_at + timedelta(minutes=12),
                    metadata_json=demo_metadata(profile, recommendation="quarantine"),
                )
            )
        else:
            session.add(
                Event(
                    user_id=user.id,
                    action="blocked",
                    ip_address=profile.last_ip,
                    country=profile.country,
                    user_agent="SentinelAI Demo Seeder/1.0",
                    trust_score_at_time=profile.trust_score,
                    timestamp=registered_at + timedelta(minutes=14),
                    metadata_json=demo_metadata(profile, recommendation="blocked"),
                )
            )

        if profile.otp_mode:
            session.add(
                OtpSession(
                    user_id=user.id,
                    otp_code="123456",
                    expires_at=registered_at + timedelta(minutes=5),
                    used=True,
                    delivery_status="delivered",
                    delivery_attempts=1,
                    last_delivery_error=None,
                )
            )
            session.add(
                Event(
                    user_id=user.id,
                    action="otp_sent",
                    ip_address=profile.last_ip,
                    country=profile.country,
                    user_agent="SentinelAI Demo Seeder/1.0",
                    trust_score_at_time=profile.trust_score,
                    timestamp=registered_at + timedelta(minutes=11),
                    metadata_json=json.dumps(
                        {
                            "demo_seed": True,
                            "delivery_mode": profile.otp_mode,
                            "delivery_status": "delivered",
                        }
                    ),
                )
            )

    session.commit()
    return seeded_ids


def seed_alerts(session, seeded_ids: dict[str, str]) -> None:
    now = utc_now_naive()
    for seed in ALERT_SEEDS:
        affected_ids = [seeded_ids[email] for email in seed["affected"] if email in seeded_ids]
        session.add(
            Alert(
                type=seed["type"],
                severity=seed["severity"],
                description=seed["description"],
                affected_user_ids=",".join(affected_ids),
                resolved=False,
                timestamp=now - timedelta(minutes=seed["minutes_ago"]),
            )
        )
    session.commit()


def main() -> int:
    args = parse_args()
    engine = build_engine(args.db_url)
    Base.metadata.create_all(bind=engine)

    from sqlalchemy.orm import sessionmaker

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        if args.reset:
            delete_demo_rows(session)

        seeded_ids = seed_users(session)
        seed_alerts(session, seeded_ids)

        trust_scores = [profile.trust_score for profile in DEMO_USERS]
        active = sum(1 for profile in DEMO_USERS if profile.status == "active")
        quarantined = sum(1 for profile in DEMO_USERS if profile.status == "quarantined")
        blocked = sum(1 for profile in DEMO_USERS if profile.status == "blocked")

        print("[success] Demo dashboard seeded.")
        print(f"[success] Users: {len(DEMO_USERS)} (active={active}, quarantined={quarantined}, blocked={blocked})")
        print(f"[success] Trust score range: {min(trust_scores)}-{max(trust_scores)}")
        print("[info] Admin login for demo:")
        print(f"       email: {ADMIN_EMAIL}")
        print(f"       password: {DEMO_PASSWORD}")
        print(f"[info] Database: {args.db_url}")
        return 0
    finally:
        session.close()


if __name__ == "__main__":
    raise SystemExit(main())
