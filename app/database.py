from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()

DB_URL = "sqlite:///cook_history.db"
engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class UserHistory(Base):
    __tablename__ = "user_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), default="demo")
    title = Column(String(200))
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    cuisine = Column(String(100))
    ingredients = Column(Text)
    ready_in_minutes = Column(Integer)