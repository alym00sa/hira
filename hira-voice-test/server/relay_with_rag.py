if"""
WebSocket relay server with RAG integration
Intercepts function calls to search the knowledge base
"""
import asyncio
import json
import os
import sys
from pathlib import Path
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


async def relay_handler(client_ws, path):
    """Handle client connection and relay to OpenAI with RAG"""
    print(f"\n🔵 Client connecting from {client_ws.remote_address}")

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

            # Configure session with HiRA instructions and tools
            session_update = {
                "type": "session.update",
                "session": {
                    "instructions": """You are HiRA (Human Rights Assistant), a voice AI specializing in human rights-based approaches.

Your personality: Warm, conversational, professional yet approachable.

CRITICAL for voice responses:
1. ALWAYS search the knowledge base when asked a question
2. Keep responses VERY BRIEF (2-3 sentences maximum for voice)
3. Speak naturally and conversationally
4. Cite 1 source if relevant
5. Be concise - people are listening, not reading

When a question is asked:
1. Call search_knowledge_base function
2. Wait for results
3. Give a short, clear answer based on the context
4. Mention the source naturally if helpful

Remember: This is VOICE. Be brief and conversational!""",
                    "tools": [{
                        "type": "function",
                        "name": "search_knowledge_base",
                        "description": "Search the human rights knowledge base. ALWAYS use this for any question about HRBA, policies, or human rights topics.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The search query"
                                }
                            },
                            "required": ["query"]
                        }
                    }],
                    "tool_choice": "auto"
                }
            }
            await openai_ws.send(json.dumps(session_update))
            print("📋 Sent HiRA configuration to OpenAI")

            # Relay messages bidirectionally with RAG interception
            async def client_to_openai():
                async for message in client_ws:
                    await openai_ws.send(message)
                    if isinstance(message, str):
                        event = json.loads(message)
                        event_type = event.get('type', 'unknown')
                        if event_type not in ['input_audio_buffer.append', 'response.create']:
                            print(f"  → {event_type}")

            async def openai_to_client():
                async for message in openai_ws:
                    if isinstance(message, str):
                        event = json.loads(message)
                        event_type = event.get('type', 'unknown')

                        # Log all events to debug
                        if 'function' in event_type.lower() or 'tool' in event_type.lower():
                            print(f"  🔍 DEBUG: {event_type}")
                            print(f"      Event: {json.dumps(event, indent=2)[:500]}")

                        # Intercept function calls for RAG
                        if event_type == "response.function_call_arguments.done":
                            func_call = event.get('item', {})
                            func_name = func_call.get('name')
                            call_id = func_call.get('call_id')

                            if func_name == "search_knowledge_base":
                                print(f"📚 RAG function called")

                                try:
                                    # Parse arguments
                                    args = json.loads(func_call.get('arguments', '{}'))
                                    query = args.get('query', '')

                                    print(f"   Query: {query}")

                                    # Search RAG
                                    context_data = rag_engine.build_context_prompt(
                                        query=query,
                                        n_results=3  # Top 3 for voice (keep it concise)
                                    )

                                    if context_data["has_context"]:
                                        result = {
                                            "context": context_data["context"],
                                            "sources": [
                                                {
                                                    "filename": src["filename"],
                                                    "similarity": round(src["similarity"], 2)
                                                }
                                                for src in context_data["sources"][:2]  # Max 2 sources for voice
                                            ]
                                        }
                                        print(f"   ✅ Found {len(context_data['sources'])} results")
                                    else:
                                        result = {
                                            "context": "No relevant information found in the knowledge base.",
                                            "sources": []
                                        }
                                        print(f"   ⚠️ No results found")

                                    # Send function result back to OpenAI
                                    function_response = {
                                        "type": "conversation.item.create",
                                        "item": {
                                            "type": "function_call_output",
                                            "call_id": call_id,
                                            "output": json.dumps(result)
                                        }
                                    }
                                    await openai_ws.send(json.dumps(function_response))

                                    # Trigger response generation
                                    await openai_ws.send(json.dumps({"type": "response.create"}))
                                    print(f"   📤 Sent results back to OpenAI")

                                except Exception as e:
                                    print(f"   ❌ RAG error: {e}")
                                    error_response = {
                                        "type": "conversation.item.create",
                                        "item": {
                                            "type": "function_call_output",
                                            "call_id": call_id,
                                            "output": json.dumps({"error": str(e)})
                                        }
                                    }
                                    await openai_ws.send(json.dumps(error_response))

                                # Don't forward function call to client
                                continue

                        # Forward all other messages
                        if event_type not in ['response.audio.delta', 'input_audio_buffer.speech_started']:
                            print(f"  ← {event_type}")

                        await client_ws.send(message)

            await asyncio.gather(client_to_openai(), openai_to_client())

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("👋 Client disconnected")


async def main():
    print("\n" + "="*60)
    print("🎤 HIRA VOICE TEST - Relay with RAG")
    print("="*60)
    print("Starting server on ws://0.0.0.0:8765")
    print("Waiting for connections...")
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
