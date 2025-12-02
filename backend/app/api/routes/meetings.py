"""
Meeting endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.models.meeting import Meeting
from app.models.schemas import MeetingCreate, MeetingUpdate, MeetingResponse, MeetingListResponse
from app.services.meeting_service import MeetingService
import uuid

router = APIRouter()

def get_meeting_service(db: Session = Depends(get_db)) -> MeetingService:
    """Dependency to get meeting service instance"""
    return MeetingService(db)

@router.post("/meetings", response_model=MeetingResponse, status_code=201)
async def create_meeting(
    meeting_data: MeetingCreate,
    meeting_service: MeetingService = Depends(get_meeting_service)
):
    """
    Create a new meeting

    - **title**: Meeting title
    - **date**: Meeting date/time
    - **transcript**: Optional transcript text
    - **participants**: Optional list of participants
    """
    try:
        meeting = await meeting_service.create_meeting(meeting_data)
        return meeting.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create meeting: {str(e)}")

@router.get("/meetings", response_model=MeetingListResponse)
async def list_meetings(
    user_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    meeting_service: MeetingService = Depends(get_meeting_service)
):
    """Get list of all meetings"""
    try:
        meetings, total = await meeting_service.list_meetings(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        return MeetingListResponse(
            meetings=[m.to_dict() for m in meetings],
            total=total
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list meetings: {str(e)}")

@router.get("/meetings/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(
    meeting_id: str,
    meeting_service: MeetingService = Depends(get_meeting_service)
):
    """Get a specific meeting by ID"""
    try:
        meeting = await meeting_service.get_meeting(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return meeting.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve meeting: {str(e)}")

@router.get("/meetings/share/{share_token}", response_model=MeetingResponse)
async def get_meeting_by_share_token(
    share_token: str,
    meeting_service: MeetingService = Depends(get_meeting_service)
):
    """Get a meeting by its public share token"""
    try:
        meeting = await meeting_service.get_meeting_by_share_token(share_token)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found or not public")
        return meeting.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve meeting: {str(e)}")

@router.patch("/meetings/{meeting_id}", response_model=MeetingResponse)
async def update_meeting(
    meeting_id: str,
    meeting_data: MeetingUpdate,
    meeting_service: MeetingService = Depends(get_meeting_service)
):
    """Update a meeting"""
    try:
        meeting = await meeting_service.update_meeting(meeting_id, meeting_data)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return meeting.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update meeting: {str(e)}")

@router.delete("/meetings/{meeting_id}")
async def delete_meeting(
    meeting_id: str,
    meeting_service: MeetingService = Depends(get_meeting_service)
):
    """Delete a meeting"""
    try:
        success = await meeting_service.delete_meeting(meeting_id)
        if not success:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return {"status": "success", "message": f"Meeting {meeting_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete meeting: {str(e)}")

@router.post("/meetings/{meeting_id}/generate-summary", response_model=MeetingResponse)
async def generate_meeting_summary(
    meeting_id: str,
    meeting_service: MeetingService = Depends(get_meeting_service)
):
    """
    Generate structured summary for a meeting using HiRA's LLM

    Extracts: key topics, action items, rights issues, risk flags, etc.
    """
    try:
        meeting = await meeting_service.generate_summary(meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return meeting.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")

@router.post("/meetings/{meeting_id}/share")
async def create_share_link(
    meeting_id: str,
    meeting_service: MeetingService = Depends(get_meeting_service)
):
    """Create a public share link for a meeting"""
    try:
        share_token = await meeting_service.create_share_token(meeting_id)
        if not share_token:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return {
            "share_token": share_token,
            "share_url": f"/meetings/share/{share_token}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create share link: {str(e)}")
