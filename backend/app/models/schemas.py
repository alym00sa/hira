"""
Pydantic schemas for API request/response models
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Chat Models
class ChatMessage(BaseModel):
    """Single chat message"""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    """Request to send a chat message"""
    message: str = Field(..., description="User's message to HiRA")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")

class ChatResponse(BaseModel):
    """Response from HiRA"""
    message: str = Field(..., description="HiRA's response")
    conversation_id: str = Field(..., description="Conversation ID")
    sources: Optional[List[dict]] = Field(default=[], description="Source documents used")
    timestamp: datetime

# Document Models
class DocumentMetadata(BaseModel):
    """Metadata for uploaded document"""
    filename: str
    file_size: int
    upload_date: datetime
    document_type: str
    processed: bool = False
    chunk_count: Optional[int] = None

class DocumentUploadResponse(BaseModel):
    """Response after document upload"""
    document_id: str
    filename: str
    status: str
    message: str
    metadata: DocumentMetadata

class DocumentListResponse(BaseModel):
    """List of documents"""
    documents: List[DocumentMetadata]
    total: int

class DocumentChunk(BaseModel):
    """A chunk of text from a document"""
    chunk_id: str
    document_id: str
    content: str
    metadata: dict
    embedding: Optional[List[float]] = None

# Source Citation Model
class SourceCitation(BaseModel):
    """Citation from a source document"""
    document_name: str
    chunk_text: str
    relevance_score: float
    page_number: Optional[int] = None

# Health Check
class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    environment: str
    rag_status: str
    vector_db_status: str

# Meeting Models
class MeetingCreate(BaseModel):
    """Request to create a new meeting"""
    title: str = Field(..., description="Meeting title")
    date: datetime = Field(..., description="Meeting date/time")
    duration_minutes: Optional[int] = Field(None, description="Duration in minutes")
    platform: str = Field(default="zoom", description="Platform (zoom, teams, etc.)")
    meeting_link: Optional[str] = Field(None, description="Meeting link/URL")
    participants: Optional[List[str]] = Field(default=[], description="List of participants")
    transcript: Optional[str] = Field(None, description="Full meeting transcript")

class MeetingUpdate(BaseModel):
    """Request to update a meeting"""
    title: Optional[str] = None
    transcript: Optional[str] = None
    summary: Optional[str] = None
    key_stakeholders: Optional[List[str]] = None
    structured_notes: Optional[dict] = None
    next_steps: Optional[List[str]] = None
    action_items: Optional[List[dict]] = None
    is_public: Optional[bool] = None

class MeetingResponse(BaseModel):
    """Meeting response"""
    id: str
    title: str
    date: str  # Changed to string to match to_dict() ISO format
    duration_minutes: Optional[int]
    platform: str
    meeting_link: Optional[str]
    participants: List[str]
    transcript: Optional[str]
    summary: Optional[str]
    key_topics: List[str]
    action_items: List[dict]
    rights_issues: List[dict]
    risk_flags: List[dict]
    obligations: List  # Can be strings or dicts (used for HiRA interactions)
    key_stakeholders: List[str]
    next_steps: List[str]
    structured_notes: dict  # Structured notes organized by topic
    share_token: Optional[str]
    is_public: bool
    processed: bool
    created_at: str  # Changed to string to match to_dict() ISO format
    updated_at: str  # Changed to string to match to_dict() ISO format

    class Config:
        from_attributes = True

class MeetingListResponse(BaseModel):
    """List of meetings"""
    meetings: List[MeetingResponse]
    total: int
