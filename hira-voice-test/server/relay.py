"""
Minimal WebSocket relay server for OpenAI Realtime API
Step 1: Just get the connection working
"""
import asyncio
import json
import os
from dotenv import load_dotenv
import websockets

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY in .env file")

print(f"✅ OpenAI API Key loaded: {OPENAI_API_KEY[:20]}...")


async def relay_handler(client_ws, path):
    """Handle client connection and relay to OpenAI"""
    print(f"\n🔵 Client connecting from {client_ws.remote_address}")
    print(f"   Path: {path}")
    print(f"   Subprotocols requested: {client_ws.request_headers.get('Sec-WebSocket-Protocol', 'none')}")

    # Connect to OpenAI
    openai_url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"

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

            # Forward session.created from OpenAI to client
            session_msg = await openai_ws.recv()
            await client_ws.send(session_msg)
            print("📤 Forwarded session.created to client")

            # Relay messages bidirectionally
            async def client_to_openai():
                async for message in client_ws:
                    await openai_ws.send(message)
                    if isinstance(message, str):
                        event = json.loads(message)
                        print(f"  → {event.get('type', 'unknown')}")

            async def openai_to_client():
                async for message in openai_ws:
                    await client_ws.send(message)
                    if isinstance(message, str):
                        event = json.loads(message)
                        print(f"  ← {event.get('type', 'unknown')}")

            await asyncio.gather(client_to_openai(), openai_to_client())

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        print("👋 Client disconnected")


async def main():
    print("\n" + "="*60)
    print("🎤 HIRA VOICE TEST - Relay Server")
    print("="*60)
    print("Starting server on ws://0.0.0.0:8765")
    print("Waiting for connections...")
    print("="*60 + "\n")

    # Accept "realtime" subprotocol from client
    async with websockets.serve(
        relay_handler,
        "0.0.0.0",
        8765,
        subprotocols=["realtime"]
    ):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
