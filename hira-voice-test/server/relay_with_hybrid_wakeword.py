"""
WebSocket relay server with RAG integration + Hybrid Wake Word Detection
Features:
- RAG function calling for knowledge base search
- Hybrid wake word: Buffers transcript and detects "hey hira"
- Meeting context awareness via transcript buffering
- Shimmer voice
"""
import asyncio
import json
import os
import re
import sys
from pathlib import Path
from collections import deque
from datetime import datetime
from dotenv import load_dotenv
import websockets

# Load environment
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY in .env file")

# Add backend to path for RAG imports
backend_path = str(Path(__file__).parent.parent.parent / "backend")
sys.path.insert(0, backend_path)

print(f"📦 Backend path: {backend_path}")
print(f"✅ OpenAI API Key loaded: {OPENAI_API_KEY[:20]}...")

# Import RAG engine
from app.rag.rag_engine import RAGEngine

rag_engine = RAGEngine()
print("✅ RAG engine initialized")


# HiRA configuration
HIRA_TOOLS = [{
    "type": "function",
    "name": "search_knowledge_base",
    "description": "Search the human rights knowledge base for information. Use this for ANY question about HRBA, human rights, policies, or related topics.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to find relevant information"
            }
        },
        "required": ["query"]
    }
}]

HIRA_INSTRUCTIONS = """You are HiRA (Human Rights Assistant), a voice AI specializing in human rights-based approaches.

IMPORTANT CONTEXT: You are in a live meeting. Use the recent conversation context provided to understand what's being discussed.

When someone asks you a question (they will say "Hey HiRA" followed by their question):
1. Use the search_knowledge_base function to find relevant information
2. Consider both the search results AND the meeting context
3. Give a BRIEF, conversational response (2-3 sentences for voice)
4. Mention a source if helpful

Be warm, professional, and concise - this is voice, not text!"""


# Transcript buffer settings
TRANSCRIPT_BUFFER_SIZE = 50  # Keep last 50 transcript items
TRANSCRIPT_CONTEXT_SIZE = 10  # Send last 10 items to OpenAI for context


class TranscriptBuffer:
    """Manages meeting transcript buffer for context awareness"""

    def __init__(self, max_size=TRANSCRIPT_BUFFER_SIZE):
        self.buffer = deque(maxlen=max_size)
        self.wake_word_pattern = re.compile(r'\b(hey|hi|hello)\s+(hira|hera|hiera)\b', re.IGNORECASE)

    def add_item(self, speaker, text, timestamp=None):
        """Add a transcript item to the buffer"""
        item = {
            "speaker": speaker,
            "text": text,
            "timestamp": timestamp or datetime.now().isoformat()
        }
        self.buffer.append(item)
        return item

    def detect_wake_word(self, text):
        """Check if text contains wake word"""
        match = self.wake_word_pattern.search(text)
        if match:
            # Extract question (everything after wake word)
            question = text[match.end():].strip()
            return True, question
        return False, None

    def get_context(self, num_items=TRANSCRIPT_CONTEXT_SIZE):
        """Get recent transcript context for OpenAI"""
        recent = list(self.buffer)[-num_items:]
        context = "\n".join([
            f"{item['speaker']}: {item['text']}"
            for item in recent
        ])
        return context

    def get_full_transcript(self):
        """Get full transcript as text"""
        return "\n".join([
            f"[{item['timestamp']}] {item['speaker']}: {item['text']}"
            for item in self.buffer
        ])


async def relay_handler(client_ws, path):
    """Handle client connection and relay to OpenAI with RAG and wake word detection"""
    print(f"\n🔵 Client connecting from {client_ws.remote_address}")

    # Create transcript buffer for this session
    transcript = TranscriptBuffer()

    openai_url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"

    try:
        async with websockets.connect(
            openai_url,
            subprotocols=["realtime"],
            extra_headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "OpenAI-Beta": "realtime=v1"
            }
        ) as openai_ws:
            print("✅ Connected to OpenAI")

            # Forward session.created
            session_msg = await openai_ws.recv()
            await client_ws.send(session_msg)
            print("📤 Forwarded session.created")

            # Relay messages bidirectionally with RAG interception
            async def client_to_openai():
                async for message in client_ws:
                    if isinstance(message, str):
                        event = json.loads(message)
                        event_type = event.get('type')

                        # Intercept ALL session.update messages and always add our tools + shimmer voice
                        if event_type == 'session.update':
                            print("🔧 Intercepting session.update")

                            # Merge client's session with our tools and instructions
                            client_session = event.get('session', {})
                            client_session['tools'] = HIRA_TOOLS
                            client_session['tool_choice'] = 'auto'
                            client_session['instructions'] = HIRA_INSTRUCTIONS
                            client_session['voice'] = 'shimmer'  # Set shimmer voice

                            # Add meeting context to instructions if available
                            if len(transcript.buffer) > 0:
                                context = transcript.get_context()
                                client_session['instructions'] = HIRA_INSTRUCTIONS + f"\n\nRECENT MEETING CONTEXT:\n{context}"
                                print(f"   📝 Added {len(transcript.buffer)} transcript items to context")

                            event['session'] = client_session
                            message = json.dumps(event)
                            print("✅ Re-applied RAG tools, shimmer voice, and meeting context")

                        if event_type not in ['input_audio_buffer.append']:
                            print(f"  → {event_type}")

                    await openai_ws.send(message)

            async def openai_to_client():
                async for message in openai_ws:
                    if isinstance(message, str):
                        event = json.loads(message)
                        event_type = event.get('type', 'unknown')

                        # Debug: Show session.updated to confirm tools
                        if event_type == 'session.updated':
                            session = event.get('session', {})
                            tools = session.get('tools', [])
                            voice = session.get('voice', 'unknown')
                            print(f"  ← session.updated (tools: {len(tools)}, voice: {voice})")
                            if tools:
                                print(f"      ✅ Tools configured: {[t.get('name') for t in tools]}")

                        # Capture user transcript for wake word detection
                        if event_type == 'conversation.item.created':
                            item = event.get('item', {})
                            if item.get('role') == 'user' and item.get('type') == 'message':
                                # Get transcript from content
                                content = item.get('content', [])
                                for c in content:
                                    if c.get('type') == 'input_text':
                                        text = c.get('text', '')
                                        transcript.add_item("User", text)
                                        print(f"   📝 Added to transcript: {text[:50]}...")

                                        # Check for wake word
                                        has_wake_word, question = transcript.detect_wake_word(text)
                                        if has_wake_word:
                                            print(f"   🎤 WAKE WORD DETECTED! Question: {question}")

                        # Capture transcript from speech
                        if event_type == 'conversation.item.input_audio_transcription.completed':
                            transcript_text = event.get('transcript', '')
                            if transcript_text:
                                transcript.add_item("User", transcript_text)
                                print(f"   📝 Transcript: {transcript_text}")

                                # Check for wake word
                                has_wake_word, question = transcript.detect_wake_word(transcript_text)
                                if has_wake_word:
                                    print(f"   🎤 WAKE WORD DETECTED! Question: {question}")

                        # Capture assistant responses
                        if event_type == 'response.done':
                            response_data = event.get('response', {})
                            output = response_data.get('output', [])
                            for item in output:
                                if item.get('role') == 'assistant':
                                    content = item.get('content', [])
                                    for c in content:
                                        if c.get('type') == 'text':
                                            text = c.get('text', '')
                                            transcript.add_item("HiRA", text)
                                            print(f"   📝 HiRA response added to transcript")

                        # Intercept function calls for RAG
                        if event_type == "response.function_call_arguments.done":
                            print(f"🔍 Function call event detected!")

                            # Try different possible structures
                            func_call = event.get('item', event)
                            func_name = func_call.get('name')
                            call_id = func_call.get('call_id', func_call.get('id'))

                            print(f"   Function name: {func_name}")
                            print(f"   Call ID: {call_id}")

                            if func_name == "search_knowledge_base":
                                print(f"📚 RAG function called!")

                                try:
                                    args = json.loads(func_call.get('arguments', '{}'))
                                    query = args.get('query', '')
                                    print(f"   Query: {query}")

                                    # Search RAG
                                    context_data = rag_engine.build_context_prompt(
                                        query=query,
                                        n_results=3
                                    )

                                    if context_data["has_context"]:
                                        result = {
                                            "context": context_data["context"][:500],  # Truncate for voice
                                            "sources": [
                                                {"filename": src["filename"]}
                                                for src in context_data["sources"][:2]
                                            ],
                                            "meeting_context": transcript.get_context(5)  # Include recent meeting context
                                        }
                                        print(f"   ✅ Found {len(context_data['sources'])} RAG results")
                                    else:
                                        result = {
                                            "context": "No information found in knowledge base",
                                            "sources": [],
                                            "meeting_context": transcript.get_context(5)
                                        }
                                        print(f"   ⚠️ No RAG results")

                                    # Send function result
                                    function_response = {
                                        "type": "conversation.item.create",
                                        "item": {
                                            "type": "function_call_output",
                                            "call_id": call_id,
                                            "output": json.dumps(result)
                                        }
                                    }
                                    await openai_ws.send(json.dumps(function_response))
                                    await openai_ws.send(json.dumps({"type": "response.create"}))
                                    print(f"   📤 Sent RAG results + meeting context to OpenAI")

                                except Exception as e:
                                    print(f"   ❌ RAG error: {e}")
                                    import traceback
                                    traceback.print_exc()

                                # Don't forward function call to client
                                continue

                        # Forward other messages
                        if event_type not in ['response.audio.delta', 'input_audio_buffer.speech_started',
                                               'input_audio_buffer.speech_stopped']:
                            print(f"  ← {event_type}")

                    await client_ws.send(message)

            await asyncio.gather(client_to_openai(), openai_to_client())

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Log final transcript stats
        print(f"📊 Session ended. Total transcript items: {len(transcript.buffer)}")
        print("👋 Client disconnected")


async def main():
    print("\n" + "="*60)
    print("🎤 HIRA VOICE - Hybrid Wake Word + RAG + Meeting Context")
    print("="*60)
    print("Features:")
    print("  - Shimmer voice")
    print("  - Hybrid wake word detection ('Hey HiRA')")
    print("  - Meeting transcript buffering")
    print("  - RAG knowledge base search")
    print("="*60)
    print("Starting server on ws://0.0.0.0:8765")
    print("="*60 + "\n")

    async with websockets.serve(
        relay_handler,
        "0.0.0.0",
        8765,
        subprotocols=["realtime"]
    ):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
