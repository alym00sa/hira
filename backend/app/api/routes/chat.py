"""
Chat endpoints for HiRA
"""
from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import ChatRequest, ChatResponse
from app.services.chat_service import ChatService
from datetime import datetime
import uuid

router = APIRouter()

def get_chat_service() -> ChatService:
    """Dependency to get chat service instance"""
    return ChatService()

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Send a message to HiRA and get a response

    - **message**: The user's message
    - **conversation_id**: Optional conversation ID for context
    """
    try:
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())

        # Get response from chat service
        response_data = await chat_service.process_message(
            message=request.message,
            conversation_id=conversation_id
        )

        return ChatResponse(
            message=response_data["message"],
            conversation_id=conversation_id,
            sources=response_data.get("sources", []),
            timestamp=datetime.now()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@router.get("/chat/history/{conversation_id}")
async def get_chat_history(
    conversation_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get chat history for a conversation"""
    try:
        history = await chat_service.get_conversation_history(conversation_id)
        return {"conversation_id": conversation_id, "messages": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")
