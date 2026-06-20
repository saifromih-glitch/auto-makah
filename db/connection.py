# 🕋 Auto Makah — Database Connection
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from db.schema import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./auto_makah.db")

# Sync engine — simpler, more reliable
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(engine, autocommit=False, autoflush=False)


def init_db():
    """Create all tables synchronously."""
    Base.metadata.create_all(bind=engine)


def get_session() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
