"""
Voice Relay Service - WebSocket relay for OpenAI Realtime API
Provides RAG-enhanced voice interactions with hybrid wake word detection
"""
import asyncio
import json
import os
import re
from collections import deque
from datetime import datetime
from typing import Optional
import websockets
from websockets.server import WebSocketServerProtocol

from app.core.config import settings
from app.rag.rag_engine import RAGEngine


# Transcript buffer settings
TRANSCRIPT_BUFFER_SIZE = 50
TRANSCRIPT_CONTEXT_SIZE = 10


class TranscriptBuffer:
    """Manages meeting transcript buffer for context awareness"""

    def __init__(self, max_size=TRANSCRIPT_BUFFER_SIZE):
        self.buffer = deque(maxlen=max_size)
        self.wake_word_pattern = re.compile(
            r'\b(hey|hi|hello)\s+(hira|hera|hiera)\b',
            re.IGNORECASE
        )

    def add_item(self, speaker: str, text: str, timestamp: Optional[str] = None):
        """Add a transcript item to the buffer"""
        item = {
            "speaker": speaker,
            "text": text,
            "timestamp": timestamp or datetime.now().isoformat()
        }
        self.buffer.append(item)
        return item

    def detect_wake_word(self, text: str):
        """Check if text contains wake word"""
        match = self.wake_word_pattern.search(text)
        if match:
            question = text[match.end():].strip()
            return True, question
        return False, None

    def get_context(self, num_items: int = TRANSCRIPT_CONTEXT_SIZE):
        """Get recent transcript context"""
        recent = list(self.buffer)[-num_items:]
        context = "\n".join([
            f"{item['speaker']}: {item['text']}"
            for item in recent
        ])
        return context


class VoiceRelayService:
    """WebSocket relay service for OpenAI Realtime API with RAG"""

    def __init__(self):
        self.rag_engine = RAGEngine()
        print("✅ Voice Relay Service initialized with RAG engine")

        # HiRA configuration
        self.HIRA_TOOLS = [{
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

        self.HIRA_INSTRUCTIONS = """You are HiRA (Human Rights Assistant), a voice AI specializing in human rights-based approaches.

IMPORTANT CONTEXT: You are in a live meeting. Use the recent conversation context provided to understand what's being discussed.

When someone asks you a question (they will say "Hey HiRA" followed by their question):
1. Use the search_knowledge_base function to find relevant information
2. Consider both the search results AND the meeting context
3. Give a BRIEF, conversational response (2-3 sentences for voice)
4. Mention a source if helpful

Be warm, professional, and concise - this is voice, not text!"""

    async def relay_handler(self, client_ws: WebSocketServerProtocol, path: str):
        """Handle client connection and relay to OpenAI with RAG"""
        print(f"\n🔵 Client connecting from {client_ws.remote_address}")

        # Create transcript buffer for this session
        transcript = TranscriptBuffer()

        openai_url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"
        openai_api_key = settings.OPENAI_API_KEY  # Use settings module (loads from .env)

        if not openai_api_key:
            print("❌ OPENAI_API_KEY not found in settings")
            await client_ws.close(1008, "Server configuration error")
            return

        try:
            async with websockets.connect(
                openai_url,
                subprotocols=["realtime"],
                extra_headers={
                    "Authorization": f"Bearer {openai_api_key}",
                    "OpenAI-Beta": "realtime=v1"
                }
            ) as openai_ws:
                print("✅ Connected to OpenAI")

                # Forward session.created
                session_msg = await openai_ws.recv()
                await client_ws.send(session_msg)
                print("📤 Forwarded session.created")

                # Relay messages bidirectionally
                async def client_to_openai():
                    async for message in client_ws:
                        if isinstance(message, str):
                            event = json.loads(message)
                            event_type = event.get('type')

                            # Intercept ALL session.update messages
                            if event_type == 'session.update':
                                print("🔧 Intercepting session.update")

                                client_session = event.get('session', {})
                                client_session['tools'] = self.HIRA_TOOLS
                                client_session['tool_choice'] = 'auto'
                                client_session['voice'] = 'shimmer'

                                # Add meeting context if available
                                instructions = self.HIRA_INSTRUCTIONS
                                if len(transcript.buffer) > 0:
                                    context = transcript.get_context()
                                    instructions += f"\n\nRECENT MEETING CONTEXT:\n{context}"
                                    print(f"   📝 Added {len(transcript.buffer)} transcript items")

                                client_session['instructions'] = instructions
                                event['session'] = client_session
                                message = json.dumps(event)
                                print("✅ Applied RAG tools, shimmer voice, and context")

                            if event_type not in ['input_audio_buffer.append']:
                                print(f"  → {event_type}")

                        await openai_ws.send(message)

                async def openai_to_client():
                    async for message in openai_ws:
                        if isinstance(message, str):
                            event = json.loads(message)
                            event_type = event.get('type', 'unknown')

                            # Log session updates
                            if event_type == 'session.updated':
                                session = event.get('session', {})
                                tools = session.get('tools', [])
                                voice = session.get('voice', 'unknown')
                                print(f"  ← session.updated (tools: {len(tools)}, voice: {voice})")
                                if tools:
                                    print(f"      ✅ Tools: {[t.get('name') for t in tools]}")

                            # Capture transcript for wake word detection
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
                                print(f"🔍 Function call detected!")

                                func_call = event.get('item', event)
                                func_name = func_call.get('name')
                                call_id = func_call.get('call_id', func_call.get('id'))

                                print(f"   Function: {func_name}, Call ID: {call_id}")

                                if func_name == "search_knowledge_base":
                                    print(f"📚 RAG function called!")

                                    try:
                                        args = json.loads(func_call.get('arguments', '{}'))
                                        query = args.get('query', '')
                                        print(f"   Query: {query}")

                                        # Search RAG
                                        context_data = self.rag_engine.build_context_prompt(
                                            query=query,
                                            n_results=3
                                        )

                                        if context_data["has_context"]:
                                            result = {
                                                "context": context_data["context"][:500],
                                                "sources": [
                                                    {"filename": src["filename"]}
                                                    for src in context_data["sources"][:2]
                                                ],
                                                "meeting_context": transcript.get_context(5)
                                            }
                                            print(f"   ✅ Found {len(context_data['sources'])} results")
                                        else:
                                            result = {
                                                "context": "No information found in knowledge base",
                                                "sources": [],
                                                "meeting_context": transcript.get_context(5)
                                            }
                                            print(f"   ⚠️ No results")

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
                                        print(f"   📤 Sent RAG results to OpenAI")

                                    except Exception as e:
                                        print(f"   ❌ RAG error: {e}")
                                        import traceback
                                        traceback.print_exc()

                                    # Don't forward function call to client
                                    continue

                            # Forward other messages
                            if event_type not in ['response.audio.delta',
                                                   'input_audio_buffer.speech_started',
                                                   'input_audio_buffer.speech_stopped']:
                                print(f"  ← {event_type}")

                        await client_ws.send(message)

                await asyncio.gather(client_to_openai(), openai_to_client())

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print(f"📊 Session ended. Total transcript items: {len(transcript.buffer)}")
            print("👋 Client disconnected")

    async def start_server(self, host: str = "0.0.0.0", port: int = 8765):
        """Start the WebSocket relay server"""
        print("\n" + "="*60)
        print("🎤 HIRA VOICE RELAY SERVICE")
        print("="*60)
        print("Features:")
        print("  - Shimmer voice")
        print("  - Hybrid wake word detection ('Hey HiRA')")
        print("  - Meeting transcript buffering")
        print("  - RAG knowledge base search")
        print("="*60)
        print(f"Starting WebSocket server on ws://{host}:{port}")
        print("="*60 + "\n")

        async with websockets.serve(
            self.relay_handler,
            host,
            port,
            subprotocols=["realtime"]
        ):
            await asyncio.Future()  # Run forever
