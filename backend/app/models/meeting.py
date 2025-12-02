"""
Meeting database models
"""
from sqlalchemy import Column, String, Text, DateTime, Integer, JSON, Boolean
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class Meeting(Base):
    """Meeting record with transcript and structured summary"""
    __tablename__ = "meetings"

    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Basic info
    title = Column(String(255), nullable=False)
    date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=True)

    # Meeting metadata
    platform = Column(String(50), default="zoom")  # zoom, teams, etc.
    meeting_link = Column(String(500), nullable=True)
    participants = Column(JSON, default=list)  # List of participant names/emails

    # Transcript (full text with speaker labels)
    transcript = Column(Text, nullable=True)

    # Structured summary (from PRD FR-8)
    summary = Column(Text, nullable=True)  # Overall summary
    key_topics = Column(JSON, default=list)  # List of main topics discussed
    action_items = Column(JSON, default=list)  # List of action items with owners
    rights_issues = Column(JSON, default=list)  # Human rights issues identified
    risk_flags = Column(JSON, default=list)  # Risk flags raised
    obligations = Column(JSON, default=list)  # Obligations identified (also used for HiRA interactions)
    key_stakeholders = Column(JSON, default=list)  # Key stakeholders mentioned
    next_steps = Column(JSON, default=list)  # Next steps identified
    structured_notes = Column(JSON, default=dict)  # Structured notes organized by topic

    # Sharing
    share_token = Column(String(50), unique=True, nullable=True)  # For public links
    is_public = Column(Boolean, default=False)

    # User association (for Phase 1, nullable; will be required later with auth)
    user_id = Column(String, nullable=True)

    # Processing status
    processed = Column(Boolean, default=False)  # Has summary been generated?

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            "id": self.id,
            "title": self.title,
            "date": self.date.isoformat() if self.date else None,
            "duration_minutes": self.duration_minutes,
            "platform": self.platform,
            "meeting_link": self.meeting_link,
            "participants": self.participants or [],
            "transcript": self.transcript,
            "summary": self.summary,
            "key_topics": self.key_topics or [],
            "action_items": self.action_items or [],
            "rights_issues": self.rights_issues or [],
            "risk_flags": self.risk_flags or [],
            "obligations": self.obligations or [],
            "key_stakeholders": self.key_stakeholders or [],
            "next_steps": self.next_steps or [],
            "structured_notes": self.structured_notes or {},
            "share_token": self.share_token,
            "is_public": self.is_public,
            "user_id": self.user_id,
            "processed": self.processed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
