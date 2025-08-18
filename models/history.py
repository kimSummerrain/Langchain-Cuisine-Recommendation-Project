from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

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