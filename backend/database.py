from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
import os

if os.getenv("VERCEL") and not os.getenv("DATABASE_URL"):
    DATABASE_URL = "sqlite:////tmp/sentinel.db"
else:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sentinel.db")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
