"""
WebSocket relay endpoint for OpenAI Realtime API (integrated into FastAPI)
"""
import asyncio
import json
import websockets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.config import settings
from app.rag.rag_engine import RAGEngine
from app.services.voice_relay_service import TranscriptBuffer

router = APIRouter()

@router.websocket("/voice-relay")
async def voice_relay_endpoint(client_ws: WebSocket):
    """
    WebSocket endpoint for voice relay
    Proxies connection between frontend and OpenAI Realtime API with RAG
    """
    await client_ws.accept()
    print(f"🔵 Voice relay client connected", flush=True)

    # Initialize RAG and transcript buffer
    try:
        print("🔧 Initializing RAG engine and transcript buffer...", flush=True)
        rag_engine = RAGEngine()
        transcript = TranscriptBuffer()
        print("✅ RAG and transcript buffer initialized", flush=True)
    except Exception as e:
        print(f"❌ Error initializing RAG: {e}", flush=True)
        import traceback
        traceback.print_exc()
        await client_ws.close(code=1011, reason="Initialization error")
        return

    # OpenAI configuration
    openai_url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"
    openai_api_key = settings.OPENAI_API_KEY

    if not openai_api_key:
        await client_ws.close(code=1008, reason="Server configuration error")
        return

    # HiRA tools and instructions (from voice_relay_service.py)
    HIRA_TOOLS = [{
        "type": "function",
        "name": "search_knowledge_base",
        "description": "Search the human rights knowledge base for information.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"}
            },
            "required": ["query"]
        }
    }]

    HIRA_INSTRUCTIONS = """You are HiRA (Human Rights Assistant), a voice AI specializing in human rights-based approaches.

CRITICAL WAKE WORD RULE: ONLY respond when you hear "Hey HiRA" at the START of speech. Stay silent otherwise.

When someone says "Hey HiRA" followed by their question:
1. Use search_knowledge_base to find information
2. Give a BRIEF, conversational response (2-3 sentences for voice)
3. Mention a source if helpful"""

    try:
        print(f"🔌 Connecting to OpenAI Realtime API...", flush=True)
        async with websockets.connect(
            openai_url,
            subprotocols=["realtime"],
            extra_headers={
                "Authorization": f"Bearer {openai_api_key}",
                "OpenAI-Beta": "realtime=v1"
            }
        ) as openai_ws:
            print("✅ Connected to OpenAI Realtime API", flush=True)

            # Start bidirectional relay immediately (don't manually forward session.created)
            # The openai_to_client task will handle session.created automatically
            print("🔄 Starting bidirectional relay tasks...", flush=True)

            async def client_to_openai():
                try:
                    while True:
                        message = await client_ws.receive_text()
                        event = json.loads(message)
                        event_type = event.get('type')

                        # Intercept session.update to add RAG tools
                        if event_type == 'session.update':
                            client_session = event.get('session', {})
                            client_session['tools'] = HIRA_TOOLS
                            client_session['tool_choice'] = 'auto'
                            client_session['voice'] = 'shimmer'
                            client_session['instructions'] = HIRA_INSTRUCTIONS
                            event['session'] = client_session

                        await openai_ws.send(json.dumps(event))
                except WebSocketDisconnect:
                    pass

            async def openai_to_client():
                try:
                    async for message in openai_ws:
                        event = json.loads(message)
                        event_type = event.get('type')

                        # Handle RAG function calls
                        if event_type == "response.function_call_arguments.done":
                            func_call = event.get('item', event)
                            func_name = func_call.get('name')
                            call_id = func_call.get('call_id', func_call.get('id'))

                            if func_name == "search_knowledge_base":
                                try:
                                    args = json.loads(func_call.get('arguments', '{}'))
                                    query = args.get('query', '')

                                    # Search RAG
                                    context_data = rag_engine.build_context_prompt(query=query, n_results=3)

                                    result = {
                                        "context": context_data.get("context", "")[:500],
                                        "sources": [{"filename": src["filename"]} for src in context_data.get("sources", [])[:2]]
                                    } if context_data.get("has_context") else {"context": "No information found", "sources": []}

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
                                    continue
                                except Exception as e:
                                    print(f"❌ RAG error: {e}")

                        await client_ws.send_text(message)
                except:
                    pass

            await asyncio.gather(client_to_openai(), openai_to_client())

    except WebSocketDisconnect:
        print("👋 Voice relay client disconnected")
    except Exception as e:
        print(f"❌ Voice relay error: {e}")
        import traceback
        traceback.print_exc()
