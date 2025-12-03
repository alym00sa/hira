"""
Simple test to verify Recall.ai chat webhooks work
Based on official Recall.ai meeting-bot example
"""
import os
import sys
import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

# Add backend to path so we can import services
sys.path.insert(0, os.path.dirname(__file__))

# Import RAG, LLM, and voice services
from app.rag.rag_engine import RAGEngine
from app.services.llm_service import LLMService
from app.services.elevenlabs_service import elevenlabs_service

# Config
RECALL_API_KEY = os.getenv("RECALL_API_KEY", "45cb49af128deb00d9883c41cc0701afb4b65824")
RECALL_REGION = "us-west-2"
API_BASE = f"https://{RECALL_REGION}.recall.ai/api/v1"
NGROK_URL = os.getenv("WEBHOOK_URL", "https://absorbable-furcately-vernia.ngrok-free.dev")

# Authorization header - use "Token" prefix like official example
HEADERS = {
    "Authorization": f"Token {RECALL_API_KEY}",
    "Content-Type": "application/json"
}

app = FastAPI()

# Initialize RAG and LLM services
rag_engine = RAGEngine()
llm_service = LLMService()

# Store conversation history per bot session
conversation_history = {}  # bot_id -> list of {"question": str, "answer": str}

@app.post("/test-webhook")
async def test_webhook(request: Request):
    """Handle incoming webhooks from Recall.ai"""
    try:
        body = await request.json()
        print("\n" + "="*60)
        print("📥 WEBHOOK RECEIVED!")
        print("="*60)

        # Print full payload for debugging
        import json
        print("FULL PAYLOAD:")
        print(json.dumps(body, indent=2))
        print("="*60)

        event_type = body.get("event") or body.get("type", "")
        print(f"Event Type: {event_type}")

        if event_type == "participant_events.chat_message":
            # Parse the nested structure correctly
            data = body.get("data", {}).get("data", {})
            participant = data.get("participant", {})
            message_data = data.get("data", {})
            message = message_data.get("text", "")
            bot_id = body.get("data", {}).get("bot", {}).get("id")

            print(f"💬 CHAT MESSAGE DETECTED!")
            print(f"   From: {participant.get('name', 'Unknown')}")
            print(f"   Message: {message}")
            print(f"   Bot ID: {bot_id}")

            # Check if message mentions HiRA
            if "hira" in message.lower():
                print(f"🎯 HIRA MENTIONED! Sending response...")

                # Extract the actual question (remove @HiRA mentions)
                question = message.replace('@HiRA', '').replace('@hira', '').replace('hira', '').replace('HiRA', '').strip()

                if question:
                    # Initialize conversation history for this bot if needed
                    if bot_id not in conversation_history:
                        conversation_history[bot_id] = []

                    # Get context from RAG
                    rag_context = rag_engine.build_context_prompt(
                        query=question,
                        user_id="test_user"
                    )

                    # Build meeting context from previous Q&A
                    meeting_context = ""
                    if conversation_history[bot_id]:
                        recent_qa = conversation_history[bot_id][-3:]  # Last 3 Q&A pairs
                        meeting_context = "\n\nPREVIOUS QUESTIONS IN THIS MEETING:\n"
                        for i, qa in enumerate(recent_qa, 1):
                            meeting_context += f"{i}. Q: {qa['question']}\n   A: {qa['answer'][:100]}...\n"
                        meeting_context += "\n(Use this context to give more relevant, conversational responses. Reference previous questions if relevant.)\n"

                    # Add Zoom meeting guidance to the question
                    enhanced_question = f"""{question}

[IMPORTANT: This is a Zoom meeting chat response. Keep it:
- BRIEF: 2-3 sentences maximum (50-75 words)
- WARM: Friendly and approachable tone
- CLEAR: Simple language, no jargon unless necessary
- ACTIONABLE: Give concrete, helpful guidance
- CONTEXTUAL: Reference previous discussion if relevant
Think of it as speaking out loud in a meeting - conversational but professional.]{meeting_context}"""

                    # Generate response using LLM service
                    result = await llm_service.generate_response(
                        user_message=enhanced_question,
                        context=rag_context
                    )
                    response_text = result["message"]

                    # Store in conversation history
                    conversation_history[bot_id].append({
                        "question": question,
                        "answer": response_text
                    })

                    # Keep only last 10 Q&A pairs to avoid memory bloat
                    if len(conversation_history[bot_id]) > 10:
                        conversation_history[bot_id] = conversation_history[bot_id][-10:]

                    # Trim if too long (for chat) - hard limit at 100 words
                    words = response_text.split()
                    if len(words) > 100:
                        response_text = " ".join(words[:100]) + "..."

                    print(f"💬 Generated response: {response_text}")
                    print(f"📊 Meeting history: {len(conversation_history[bot_id])} Q&A pairs")
                else:
                    response_text = "Hi! How can I help you? Just ask me a question!"

                # Generate and send voice response
                try:
                    print(f"🎤 Generating audio...")
                    audio_base64 = elevenlabs_service.text_to_speech_base64(response_text)
                    print(f"🔊 Sending audio to meeting...")
                    output_audio(audio_base64, bot_id)
                    print(f"✅ Audio sent successfully!")
                except Exception as e:
                    print(f"⚠️ Voice failed, using chat only: {str(e)}")

                # Also send in chat
                send_chat_message(bot_id, f"🌍 {response_text}")
        else:
            print(f"Other event: {event_type}")

        print("="*60 + "\n")
        return JSONResponse({"ok": True})

    except Exception as e:
        print(f"❌ Error in webhook: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse({"ok": False, "error": str(e)})

def send_chat_message(bot_id: str, message: str):
    """Send a chat message through the bot"""
    url = f"{API_BASE}/bot/{bot_id}/send_chat_message/"

    try:
        response = requests.post(
            url,
            headers=HEADERS,
            json={"message": message, "send_to": "everyone"},
            timeout=10
        )
        response.raise_for_status()
        print(f"   ✅ Chat message sent: {message[:50]}...")
    except Exception as e:
        print(f"   ❌ Failed to send chat message: {e}")

def output_audio(audio_base64: str, bot_id: str):
    """Send audio to play in the meeting"""
    url = f"{API_BASE}/bot/{bot_id}/output_audio/"

    try:
        response = requests.post(
            url,
            headers=HEADERS,
            json={"b64_data": audio_base64, "kind": "mp3"},
            timeout=30
        )
        response.raise_for_status()
        print(f"   ✅ Audio output sent ({len(audio_base64)} bytes)")
    except Exception as e:
        print(f"   ❌ Failed to send audio: {e}")
        raise

@app.post("/create-test-bot")
async def create_test_bot(payload: dict):
    """Create a test bot with proper webhook configuration"""
    meeting_url = payload["meeting_url"]
    bot_name = payload.get("bot_name", "HiRA Test")

    # Configure webhook endpoint - following official example pattern
    endpoints = [{
        "type": "webhook",
        "url": f"{NGROK_URL}/test-webhook",
        "events": [
            "participant_events.chat_message",
            "participant_events.join",
            "participant_events.leave"
        ]
    }]

    # Recording config - following official example
    recording_config = {
        "transcript": {
            "provider": {
                "recallai_streaming": {
                    "language_code": "en",
                    "mode": "prioritize_low_latency"
                }
            }
        },
        "participant_events": {},
        "meeting_metadata": {},
        "realtime_endpoints": endpoints,
        "start_recording_on": "participant_join"
    }

    body = {
        "meeting_url": meeting_url,
        "bot_name": bot_name,
        "recording_config": recording_config
    }

    print("\n" + "="*60)
    print("🚀 CREATING TEST BOT")
    print("="*60)
    print(f"Meeting URL: {meeting_url}")
    print(f"Bot Name: {bot_name}")
    print(f"Webhook URL: {NGROK_URL}/test-webhook")
    print(f"Events: participant_events.chat_message")
    print("="*60 + "\n")

    try:
        response = requests.post(
            f"{API_BASE}/bot/",
            headers=HEADERS,
            json=body,
            timeout=30
        )
        response.raise_for_status()

        bot_data = response.json()
        bot_id = bot_data.get("id")

        print(f"✅ Bot created successfully!")
        print(f"   Bot ID: {bot_id}")
        print(f"\nNow try typing in the meeting:")
        print(f"   @HiRA test message")
        print(f"\nWatch this terminal for webhook logs!\n")

        return JSONResponse({
            "success": True,
            "bot_id": bot_id,
            "webhook_url": f"{NGROK_URL}/test-webhook"
        })

    except requests.exceptions.HTTPError as e:
        print(f"❌ Failed to create bot: {e}")
        print(f"   Response: {e.response.text}")
        return JSONResponse({
            "success": False,
            "error": str(e),
            "response": e.response.text
        }, status_code=500)

@app.get("/")
async def root():
    return {
        "message": "Recall.ai Chat Test Server",
        "endpoints": {
            "create_bot": "POST /create-test-bot",
            "webhook": "POST /test-webhook"
        },
        "ngrok_url": NGROK_URL
    }

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 RECALL.AI CHAT TEST SERVER")
    print("="*60)
    print(f"NGROK URL: {NGROK_URL}")
    print(f"Webhook: {NGROK_URL}/test-webhook")
    print(f"API Region: {RECALL_REGION}")
    print("="*60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)
