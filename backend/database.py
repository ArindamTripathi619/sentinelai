from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
import os

# Primary dev DB is PostgreSQL (via docker-compose). Falls back to SQLite
# when `DATABASE_URL` is unset for zero-setup convenience.
# DATABASE_URL=postgresql+psycopg2://sentinelai:sentinelai@127.0.0.1:5432/sentinelai
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sentinel.db")

def is_sqlite_url(database_url: str) -> bool:
    return database_url.startswith("sqlite")


def build_engine(database_url: str):
    engine_kwargs = {}
    if is_sqlite_url(database_url):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    else:
        engine_kwargs["pool_pre_ping"] = True
        engine_kwargs["pool_recycle"] = int(os.getenv("DB_POOL_RECYCLE", "3600"))
        engine_kwargs["pool_size"] = int(os.getenv("DB_POOL_SIZE", "20"))
        engine_kwargs["max_overflow"] = int(os.getenv("DB_POOL_OVERFLOW", "20"))

    return create_engine(database_url, **engine_kwargs)


engine = build_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
