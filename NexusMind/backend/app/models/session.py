from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
import datetime
import uuid


class Session(Base):
    """Persistent record of a user's NexusMind session."""
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True, nullable=False)
    goal = Column(Text, nullable=False)
    status = Column(String, default="initialized")  # initialized | planning | executing | completed | failed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    # Relationship — Task model defined in app.models.task
    tasks = relationship(
        "Task",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
