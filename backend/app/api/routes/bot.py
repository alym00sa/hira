"""
Zoom Bot endpoints using Recall.ai
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
from datetime import datetime
import asyncio

from app.services.recall_service import recall_service
from app.services.deepgram_service import DeepgramService
from app.services.elevenlabs_service import elevenlabs_service
from app.services.llm_service import LLMService
from app.rag.rag_engine import RAGEngine
from app.core.database import SessionLocal
from app.services.meeting_service import MeetingService
from app.models.schemas import MeetingCreate

router = APIRouter()

# Initialize services
llm_service = LLMService()
rag_engine = RAGEngine()

# Store active bot sessions
active_sessions = {}

# Store conversation history per bot session
conversation_history = {}  # bot_id -> list of {"question": str, "answer": str}

def detect_trigger(text: str) -> bool:
    """Check if text contains a trigger phrase for HiRA"""
    triggers = [
        "hey hira",
        "hi hira",
        "hira",
        "@hira",
        "hey hera",  # Common mishearing
        "hi hera"
    ]
    text_lower = text.lower()
    return any(trigger in text_lower for trigger in triggers)

async def handle_question(question: str, bot_id: str, use_voice: bool = True):
    """
    Handle a question directed at HiRA with full context awareness

    Args:
        question: The question text
        bot_id: Bot ID to send response to
        use_voice: Whether to use voice response (False for chat)
    """
    try:
        print(f"❓ Question detected: {question}")

        # Initialize conversation history for this bot if needed
        if bot_id not in conversation_history:
            conversation_history[bot_id] = []

        # Get bot session for live transcript
        session = active_sessions.get(bot_id, {})
        meeting_id = session.get('meeting_id')

        # 1. Get live meeting context (last 10 segments ~2-3 minutes)
        live_transcript = " ".join(session.get('transcript', [])[-10:])
        meeting_context = ""
        if live_transcript:
            meeting_context = f"""
CURRENT MEETING CONTEXT (what's been said recently):
{live_transcript}
"""
            print(f"📝 Using {len(session.get('transcript', []))} transcript segments")

        # 2. Build meeting Q&A context from conversation history
        qa_context = ""
        if conversation_history[bot_id]:
            recent_qa = conversation_history[bot_id][-3:]  # Last 3 Q&A pairs
            qa_context = "\n\nPREVIOUS QUESTIONS IN THIS MEETING:\n"
            for i, qa in enumerate(recent_qa, 1):
                qa_context += f"{i}. Q: {qa['question']}\n   A: {qa['answer'][:100]}...\n"
            qa_context += "\n(Use this to give contextual responses and reference previous discussion if relevant.)\n"
            print(f"📊 Meeting history: {len(conversation_history[bot_id])} Q&A pairs")

        # 3. Search relevant previous meetings (only if relevant)
        past_meetings_context = ""
        db = SessionLocal()
        try:
            meeting_service_instance = MeetingService(db)
            relevant_meetings = await meeting_service_instance.search_relevant_meetings(
                query=question,
                limit=2,  # Top 2 most relevant
                exclude_meeting_id=meeting_id
            )

            if relevant_meetings:
                past_meetings_text = []
                for m in relevant_meetings:
                    meeting_summary = f"""
Meeting: {m['title']} ({m['date']})
Summary: {m['summary']}
Key Topics: {', '.join(m['key_topics'][:3])}"""
                    if m['action_items']:
                        meeting_summary += f"\nAction Items: {', '.join([str(item) for item in m['action_items'][:2]])}"
                    past_meetings_text.append(meeting_summary)

                past_meetings_context = f"""
RELEVANT PREVIOUS MEETINGS:
{''.join(past_meetings_text)}
"""
                print(f"📚 Using {len(relevant_meetings)} relevant past meetings")
        finally:
            db.close()

        # 4. Get context from RAG knowledge base
        rag_context = rag_engine.build_context_prompt(
            query=question,
            user_id="bot_user"
        )
        knowledge_base_context = f"""
KNOWLEDGE BASE DOCUMENTS:
{rag_context}
"""

        # Build enhanced question with Zoom meeting guidance
        enhanced_question = f"""{question}

[IMPORTANT: This is a Zoom meeting chat response. Keep it:
- BRIEF: 2-3 sentences maximum (50-75 words)
- WARM: Friendly and approachable tone
- CLEAR: Simple language, no jargon unless necessary
- ACTIONABLE: Give concrete, helpful guidance
- CONTEXTUAL: Reference previous discussion if relevant
Think of it as speaking out loud in a meeting - conversational but professional.]{qa_context}"""

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

        print(f"💬 HiRA response: {response_text}")

        # Send voice response (only if use_voice is True)
        if use_voice:
            try:
                audio_base64 = elevenlabs_service.text_to_speech_base64(response_text)
                recall_service.output_audio(audio_base64, bot_id=bot_id)
            except Exception as e:
                print(f"⚠️ Voice failed, using chat only: {str(e)}")

        # Send in chat
        recall_service.send_chat_message(
            f"🌍 {response_text}",
            bot_id=bot_id
        )

        print("✅ Response delivered!")

    except Exception as e:
        print(f"❌ Error handling question: {str(e)}")
        # Send error message
        try:
            recall_service.send_chat_message(
                "Sorry, I encountered an error processing that question.",
                bot_id=bot_id
            )
        except:
            pass

class StartBotRequest(BaseModel):
    meeting_url: str
    meeting_title: Optional[str] = None
    bot_name: str = "HiRA"
    output_media: Optional[str] = None  # URL to voice interface page

class BotSessionResponse(BaseModel):
    bot_id: str
    meeting_id: str
    status: str
    message: str

@router.post("/bot/start", response_model=BotSessionResponse)
async def start_bot(request: StartBotRequest):
    """
    Start HiRA bot and join a Zoom meeting

    The bot will:
    1. Join the Zoom meeting via Recall.ai
    2. Stream audio to our WebSocket endpoint
    3. Transcribe in real-time with Deepgram
    4. Save transcript and generate summary when done
    """
    try:
        # Create a meeting record
        meeting_id = str(uuid.uuid4())
        meeting_title = request.meeting_title or f"Meeting {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        # Create bot via Recall.ai with optional voice interface
        bot_response = recall_service.create_bot(
            meeting_url=request.meeting_url,
            bot_name=request.bot_name,
            output_media=request.output_media  # Voice interface URL if provided
        )

        bot_id = bot_response.get('id')

        # Store session info
        active_sessions[bot_id] = {
            'meeting_id': meeting_id,
            'meeting_title': meeting_title,
            'transcript': [],
            'start_time': datetime.now().isoformat()
        }

        # Send introduction message to meeting
        try:
            recall_service.send_chat_message(
                f"👋 Hi! I'm {request.bot_name}, your Human Rights Assistant. I'll be taking notes and can answer questions when you say 'Hey HiRA'.",
                bot_id=bot_id
            )
        except Exception as e:
            print(f"⚠️ Could not send intro message: {str(e)}")

        return BotSessionResponse(
            bot_id=bot_id,
            meeting_id=meeting_id,
            status="joining",
            message=f"HiRA is joining the meeting. Bot ID: {bot_id}"
        )

    except Exception as e:
        print(f"❌ Failed to start bot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bot/{bot_id}/stop")
async def stop_bot(bot_id: str):
    """
    Stop the bot and finalize the meeting

    This will:
    1. Make the bot leave the meeting
    2. Save the transcript
    3. Generate a summary
    """
    try:
        if bot_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Bot session not found")

        session = active_sessions[bot_id]

        # Make bot leave
        recall_service.leave_meeting(bot_id=bot_id)

        # Get transcript
        transcript = " ".join(session['transcript'])

        # Create meeting record
        meeting_data = MeetingCreate(
            title=session['meeting_title'],
            date=session['start_time'],
            transcript=transcript
        )

        meeting = await meeting_service.create_meeting(meeting_data)

        # Generate summary
        await meeting_service.generate_summary(meeting.id)

        # Clean up session
        del active_sessions[bot_id]

        return {
            "status": "stopped",
            "meeting_id": meeting.id,
            "message": "Bot left meeting and summary generated",
            "transcript_length": len(transcript)
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Failed to stop bot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bot/{bot_id}/status")
async def get_bot_status(bot_id: str):
    """Get current status of the bot"""
    try:
        # Get status from Recall.ai
        recall_status = recall_service.get_bot_status(bot_id)

        # Get local session info
        session = active_sessions.get(bot_id, {})

        return {
            "bot_id": bot_id,
            "recall_status": recall_status.get('status', 'unknown'),
            "meeting_id": session.get('meeting_id'),
            "transcript_segments": len(session.get('transcript', [])),
            "start_time": session.get('start_time')
        }

    except Exception as e:
        print(f"❌ Failed to get bot status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bot/chat-webhook")
async def chat_webhook(request: Request):
    """
    Webhook for Recall.ai chat events

    Handles participant_events.chat_message events
    """
    try:
        body = await request.json()
        print(f"📥 Webhook received")

        event_type = body.get("event") or body.get("type", "")  # Match working test format

        # Handle chat message events
        if event_type == "participant_events.chat_message":
            # Parse the nested structure correctly (based on actual Recall.ai webhook format)
            data = body.get("data", {}).get("data", {})
            participant = data.get("participant", {})
            message_data = data.get("data", {})
            message_text = message_data.get("text", "")
            bot_id = body.get("data", {}).get("bot", {}).get("id")

            print(f"💬 Chat message from {participant.get('name', 'Unknown')}: {message_text}")

            # Skip if no message or bot's own messages
            if not message_text or not bot_id:
                return {"status": "ignored", "reason": "no_message"}

            # Check if message mentions HiRA
            if "hira" in message_text.lower():
                print(f"🎯 HiRA mentioned in chat!")

                # Extract question (remove @HiRA mentions)
                question = message_text.replace('@HiRA', '').replace('@hira', '').replace('hira', '').replace('HiRA', '').strip()

                if question:
                    # Handle the question asynchronously
                    asyncio.create_task(handle_question(
                        question=question,
                        bot_id=bot_id,
                        use_voice=False  # No voice for chat
                    ))
                else:
                    # Just acknowledged
                    recall_service.send_chat_message(
                        "Hi! How can I help you? Just ask me a question!",
                        bot_id=bot_id
                    )

        return {"status": "processed"}

    except Exception as e:
        print(f"❌ Chat webhook error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

@router.websocket("/bot/audio")
async def audio_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for receiving audio from Recall.ai

    Recall.ai streams raw PCM audio here, which we:
    1. Forward to Deepgram for transcription
    2. Store transcript segments
    3. Process for trigger detection (future: "Hey HiRA")
    """
    await websocket.accept()
    print("🎤 Audio WebSocket connected")

    # Create Deepgram service for this session
    deepgram = DeepgramService()

    # Find the bot session (Recall.ai doesn't send bot_id in audio stream)
    # For now, use the most recent session
    # TODO: Improve session matching
    current_bot_id = list(active_sessions.keys())[-1] if active_sessions else None

    if not current_bot_id:
        print("⚠️ No active bot session found")
        await websocket.close()
        return

    session = active_sessions[current_bot_id]

    # Callback for transcript segments
    def on_transcript(text: str):
        session['transcript'].append(text)
        print(f"📝 Added to transcript: {text}")

        # Check for triggers
        if detect_trigger(text):
            print(f"🎯 Trigger detected in: {text}")
            # Handle the question asynchronously
            import asyncio
            asyncio.create_task(handle_question(text, current_bot_id))

    try:
        # Start Deepgram transcription
        await deepgram.start_transcription(on_transcript)

        # Receive audio and forward to Deepgram
        while True:
            # Receive audio bytes from Recall.ai
            message = await websocket.receive()

            if message["type"] == "websocket.disconnect":
                break

            # Audio comes as bytes
            if "bytes" in message:
                audio_data = message["bytes"]
                # Forward to Deepgram
                await deepgram.send_audio(audio_data)

    except WebSocketDisconnect:
        print("🔌 Audio WebSocket disconnected")
    except Exception as e:
        print(f"❌ WebSocket error: {str(e)}")
    finally:
        # Stop Deepgram transcription
        await deepgram.stop_transcription()
        await websocket.close()
        print("✅ Audio WebSocket closed")
