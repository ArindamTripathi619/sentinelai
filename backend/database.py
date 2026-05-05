import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base


def _build_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    # Local development fallback only - SQLite
    return "sqlite:///./sentinel.db"


DATABASE_URL = _build_database_url()

engine_kwargs = {"pool_pre_ping": True}
connect_args = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False
elif "sslmode" not in DATABASE_URL:
    separator = "&" if "?" in DATABASE_URL else "?"
    DATABASE_URL = f"{DATABASE_URL}{separator}sslmode=require"

print(f"[DATABASE] Using: {DATABASE_URL[:50]}...", file=__import__('sys').stderr)

engine = create_engine(DATABASE_URL, connect_args=connect_args, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database - create tables if they don't exist."""
    try:
        Base.metadata.create_all(bind=engine)
        print(f"[DATABASE] Tables initialized", file=__import__('sys').stderr)
    except Exception as e:
        if "could not connect" in str(e).lower() or "connection refused" in str(e).lower():
            print(f"[DATABASE] Connection failed (may retry later): {e}", file=__import__('sys').stderr)
        else:
            raise


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
