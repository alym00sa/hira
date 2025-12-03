"""
WebSocket relay endpoint for OpenAI Realtime API (integrated into FastAPI)
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.voice_relay_service import VoiceRelayService

router = APIRouter()
voice_relay = VoiceRelayService()

@router.websocket("/voice-relay")
async def voice_relay_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for voice relay
    Proxies connection between frontend and OpenAI Realtime API
    """
    await websocket.accept()
    print(f"🔵 Voice relay client connected from {websocket.client}")

    try:
        # Use the existing relay handler logic
        await voice_relay.relay_handler(websocket, "/voice-relay")
    except WebSocketDisconnect:
        print("👋 Voice relay client disconnected")
    except Exception as e:
        print(f"❌ Voice relay error: {e}")
        import traceback
        traceback.print_exc()
