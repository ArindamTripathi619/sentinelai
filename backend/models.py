# SentinelAI — Database Models
# App-owned tables backed by Supabase Postgres.

from datetime import datetime
import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, JSON, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def new_id():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=new_id)
    email = Column(String, unique=True, nullable=False)
    trust_score = Column(Integer, default=100)
    status = Column(String, default="active")  # active | quarantined | blocked
    registered_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    last_ip = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)

    # Behavioral snapshot at registration
    typing_variance_ms = Column(Float, nullable=True)
    time_to_complete_sec = Column(Float, nullable=True)
    mouse_move_count = Column(Integer, nullable=True)
    keypress_count = Column(Integer, nullable=True)

    # ML output at registration
    ml_anomaly_score = Column(Float, nullable=True)
    triggered_flags = Column(JSON, nullable=False, default=list)


class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, default=new_id)
    user_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    ip_address = Column(String, nullable=True)
    country = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    trust_score_at_time = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata_json = Column(JSON, nullable=False, default=dict)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=new_id)
    type = Column(String, nullable=False)
    severity = Column(String, nullable=False)  # low | medium | high | critical
    description = Column(String, nullable=True)
    affected_user_ids = Column(JSON, nullable=False, default=list)
    resolved = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
