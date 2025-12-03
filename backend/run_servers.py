"""
Run both FastAPI and WebSocket Voice Relay servers concurrently
"""
import asyncio
import uvicorn
from multiprocessing import Process
from app.services.voice_relay_service import VoiceRelayService


def run_fastapi():
    """Run FastAPI server"""
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False  # Disable reload in production
    )


async def run_voice_relay():
    """Run WebSocket voice relay server"""
    relay_service = VoiceRelayService()
    await relay_service.start_server(host="0.0.0.0", port=8765)


def main():
    """Start both servers"""
    print("\n" + "="*70)
    print("🚀 STARTING HIRA BACKEND SERVICES")
    print("="*70)
    print("  📡 FastAPI server will run on: http://0.0.0.0:8000")
    print("  🎤 Voice Relay will run on: ws://0.0.0.0:8765")
    print("="*70 + "\n")

    # Start FastAPI in a separate process
    fastapi_process = Process(target=run_fastapi)
    fastapi_process.start()

    # Run WebSocket relay in main process
    try:
        asyncio.run(run_voice_relay())
    except KeyboardInterrupt:
        print("\n👋 Shutting down services...")
        fastapi_process.terminate()
        fastapi_process.join()


if __name__ == "__main__":
    main()
