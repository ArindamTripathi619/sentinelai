import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base


def _build_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    # Local development fallback only.
    return "sqlite:///./sentinel.db"


DATABASE_URL = _build_database_url()

engine_kwargs = {"pool_pre_ping": True}
connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
elif "sslmode" not in DATABASE_URL:
    separator = "&" if "?" in DATABASE_URL else "?"
    DATABASE_URL = f"{DATABASE_URL}{separator}sslmode=require"

engine = create_engine(DATABASE_URL, connect_args=connect_args, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
