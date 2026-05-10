from sqlalchemy import Column, String, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import datetime
import uuid


class Task(Base):
    """Persistent audit record for each task in a session's task graph."""
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(String, nullable=False)          # planner-assigned ID (e.g. "task_001")
    description = Column(Text, nullable=False)
    skill_tag = Column(String, nullable=False)
    status = Column(String, default="pending")        # pending | running | done | failed
    output = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    session = relationship("Session", back_populates="tasks")
