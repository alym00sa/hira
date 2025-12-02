"""
Zoom Bot webhook endpoints
"""
from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
import hashlib
import hmac
import json
from app.core.config import settings

router = APIRouter()

@router.post("/zoom/webhook")
async def zoom_webhook(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    Main webhook endpoint for Zoom bot events

    Handles:
    - URL validation (challenge-response)
    - Bot events (joined, audio, etc.)
    """
    try:
        body = await request.body()
        body_str = body.decode('utf-8')

        # Parse JSON
        try:
            payload = json.loads(body_str)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON")

        # Log the event
        event_type = payload.get('event')
        print(f"📥 Zoom webhook received: {event_type}")
        print(f"   Payload: {json.dumps(payload, indent=2)}")

        # Handle URL validation (Zoom sends this when you save the endpoint URL)
        if event_type == "endpoint.url_validation":
            return handle_url_validation(payload)

        # Verify the request is from Zoom
        if not verify_zoom_request(body_str, authorization):
            raise HTTPException(status_code=401, detail="Invalid signature")

        # Handle different bot events
        if event_type == "bot_notification":
            return await handle_bot_notification(payload)

        return {"status": "received"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Zoom webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def handle_url_validation(payload: dict):
    """
    Handle Zoom's URL validation challenge

    Zoom sends a plainToken and expects an encryptedToken back
    """
    plain_token = payload.get("payload", {}).get("plainToken")

    if not plain_token:
        raise HTTPException(status_code=400, detail="No plainToken provided")

    # Encrypt the token with verification token
    encrypted_token = hmac.new(
        settings.ZOOM_VERIFICATION_TOKEN.encode(),
        plain_token.encode(),
        hashlib.sha256
    ).hexdigest()

    print(f"✅ URL Validation successful")

    return {
        "plainToken": plain_token,
        "encryptedToken": encrypted_token
    }

def verify_zoom_request(body: str, authorization: Optional[str]) -> bool:
    """
    Verify the request signature from Zoom

    For production security
    """
    # During development, we'll trust the verification token check
    # In production, verify HMAC signature from authorization header

    if not settings.DEBUG:
        # TODO: Implement full signature verification for production
        if not authorization:
            return False

    return True

async def handle_bot_notification(payload: dict):
    """
    Handle bot notification events

    Events include:
    - bot_invited
    - bot_joined_meeting
    - audio_available
    - bot_left_meeting
    """
    notification_payload = payload.get("payload", {})
    event = notification_payload.get("event")

    print(f"🤖 Bot event: {event}")

    if event == "bot_joined_meeting":
        meeting_id = notification_payload.get("object", {}).get("id")
        print(f"✅ HiRA joined meeting: {meeting_id}")
        # TODO: Initialize transcription service

    elif event == "audio_available":
        print(f"🎤 Audio stream available")
        # TODO: Start processing audio

    elif event == "bot_left_meeting":
        meeting_id = notification_payload.get("object", {}).get("id")
        print(f"👋 HiRA left meeting: {meeting_id}")
        # TODO: Finalize transcript and generate summary

    return {"status": "processed"}

@router.get("/zoom/status")
async def zoom_status():
    """Check Zoom bot configuration status"""
    return {
        "status": "configured" if settings.ZOOM_CLIENT_ID else "not_configured",
        "client_id": settings.ZOOM_CLIENT_ID[:8] + "..." if settings.ZOOM_CLIENT_ID else None,
        "has_verification_token": bool(settings.ZOOM_VERIFICATION_TOKEN),
        "has_bot_jid": bool(settings.ZOOM_BOT_JID)
    }
