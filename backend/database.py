from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
import os

# By default the project falls back to a local SQLite DB for convenience.
# For development and testing we recommend running a local Postgres and setting
# the `DATABASE_URL` env var, e.g.:
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
