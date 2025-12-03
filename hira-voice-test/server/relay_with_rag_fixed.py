"""
WebSocket relay server with RAG integration - Fixed
Intercepts and merges session updates to ensure tools are configured
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

CRITICAL: When someone asks a question, you MUST:
1. Use the search_knowledge_base function to find information
2. Wait for the search results
3. Answer based on the context provided
4. Keep responses BRIEF (2-3 sentences for voice)
5. Mention one source if helpful

Be warm, conversational, and concise - this is voice, not text!"""


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
            print("📤 Forwarded session.created")

            # Relay messages bidirectionally with RAG interception
            async def client_to_openai():
                async for message in client_ws:
                    if isinstance(message, str):
                        event = json.loads(message)
                        event_type = event.get('type')

                        # Intercept ALL session.update messages and always add our tools
                        if event_type == 'session.update':
                            print("🔧 Intercepting session.update")

                            # Merge client's session with our tools and instructions
                            client_session = event.get('session', {})
                            client_session['tools'] = HIRA_TOOLS
                            client_session['tool_choice'] = 'auto'
                            client_session['instructions'] = HIRA_INSTRUCTIONS

                            event['session'] = client_session
                            message = json.dumps(event)
                            print("✅ Re-applied RAG tools to session")

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
                            print(f"  ← session.updated (tools: {len(tools)})")
                            if tools:
                                print(f"      ✅ Tools configured: {[t.get('name') for t in tools]}")

                        # Intercept function calls for RAG
                        if event_type == "response.function_call_arguments.done":
                            print(f"🔍 Function call event detected!")
                            print(f"   Event keys: {list(event.keys())}")
                            print(f"   Full event: {json.dumps(event, indent=2)[:500]}")

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
                                            ]
                                        }
                                        print(f"   ✅ Found {len(context_data['sources'])} results")
                                    else:
                                        result = {"context": "No information found", "sources": []}
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
                                    print(f"   📤 Sent results to OpenAI")

                                except Exception as e:
                                    print(f"   ❌ RAG error: {e}")

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
        print("👋 Client disconnected")


async def main():
    print("\n" + "="*60)
    print("🎤 HIRA VOICE TEST - Relay with RAG (Fixed)")
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
