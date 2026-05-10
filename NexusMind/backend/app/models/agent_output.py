from sqlalchemy import Column, String, Text, JSON, DateTime, Float, ForeignKey
from app.database import Base
import datetime
import uuid


class AgentOutput(Base):
    """Stores the raw JSON output produced by each agent for audit and retrieval."""
    __tablename__ = "agent_outputs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(String, nullable=False)          # matches TaskGraph task_id
    agent_name = Column(String, nullable=False)
    skill_tag = Column(String, nullable=False)
    output = Column(JSON, nullable=True)
    quality_score = Column(Float, nullable=True)      # 0-100, filled by CriticAgent
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
