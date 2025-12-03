"""
Voice Test Server - WebSocket server for audio streaming
Handles audio from client, processes with STT/LLM/TTS, sends back
"""
import asyncio
import json
import os
import sys
from pathlib import Path
import websockets
from websockets.server import serve
from dotenv import load_dotenv

# Add parent directory to path to import from backend
parent_dir = str(Path(__file__).parent.parent / "backend")
sys.path.insert(0, parent_dir)

print(f"📦 Added to path: {parent_dir}")

# Load .env from backend folder
env_path = Path(parent_dir) / ".env"
load_dotenv(dotenv_path=env_path)
print(f"🔑 Loaded .env from: {env_path}")
print(f"   Deepgram key: {os.getenv('DEEPGRAM_API_KEY', 'NOT SET')[:20]}...")
print(f"   ElevenLabs key: {os.getenv('ELEVENLABS_API_KEY', 'NOT SET')[:20]}...")

# Try to import services (optional for now)
try:
    from app.services.deepgram_service import DeepgramService
    from app.services.elevenlabs_service import elevenlabs_service
    from app.services.llm_service import LLMService
    from app.rag.rag_engine import RAGEngine
    SERVICES_AVAILABLE = True
    print("✅ Services imported successfully")
except ImportError as e:
    print(f"⚠️  Services not available (will run in echo mode): {e}")
    SERVICES_AVAILABLE = False

# Configuration
HOST = "0.0.0.0"
PORT = 8765

# Initialize services if available
if SERVICES_AVAILABLE:
    deepgram_service = DeepgramService()
    llm_service = LLMService()
    rag_engine = RAGEngine()
    print("🎤 Deepgram, LLM, and RAG services initialized")

# Track active connections and audio buffers
active_connections = set()
audio_buffers = {}  # client_id -> list of audio chunks
last_audio_time = {}  # client_id -> timestamp

async def process_audio_buffer(client_id, websocket):
    """Process accumulated audio chunks with STT and TTS"""
    if client_id not in audio_buffers or not audio_buffers[client_id]:
        return

    try:
        # Get accumulated audio chunks
        chunks = audio_buffers[client_id]
        audio_buffers[client_id] = []  # Clear buffer

        # Combine all chunks into one audio blob
        audio_data = b''.join(chunks)
        print(f"\n🎤 Processing {len(chunks)} chunks ({len(audio_data)} bytes) from {client_id}")

        if not SERVICES_AVAILABLE:
            print("⚠️  Services not available, skipping STT/TTS")
            return

        # Save audio to temporary file for Deepgram
        import tempfile
        import os

        # Create temp file and close it properly before pydub reads it
        temp_fd, temp_webm_path = tempfile.mkstemp(suffix='.webm')
        try:
            os.write(temp_fd, audio_data)
            os.close(temp_fd)  # Close the file descriptor

            # Convert WebM to WAV for Deepgram
            print("🔄 Converting WebM to WAV...")
            try:
                from pydub import AudioSegment
                audio = AudioSegment.from_file(temp_webm_path, format="webm")
                audio = audio.set_frame_rate(16000).set_channels(1)  # 16kHz mono for Deepgram
                temp_wav_path = temp_webm_path.replace('.webm', '.wav')
                audio.export(temp_wav_path, format="wav")
                print("✅ Converted to WAV")
            except FileNotFoundError as e:
                print("❌ FFmpeg not found! Please install ffmpeg:")
                print("   Option 1: winget install -e --id Gyan.FFmpeg")
                print("   Option 2: Download from https://ffmpeg.org/download.html")
                print("   Make sure ffmpeg is in your system PATH")
                return

            # STEP 1: Speech-to-Text with Deepgram
            print("🎤 Transcribing with Deepgram...")
            transcript = await deepgram_service.transcribe_file(temp_wav_path)
            print(f"📝 Transcript: \"{transcript}\"")

            if not transcript or transcript.strip() == "":
                print("   No speech detected")
                return

            # Send transcript to client
            await websocket.send(json.dumps({
                "type": "transcript",
                "text": transcript
            }))

            # STEP 2: Generate response (simple for now)
            response_text = f"You said: {transcript}"
            print(f"💬 Response: \"{response_text}\"")

            # Send response text to client
            await websocket.send(json.dumps({
                "type": "response",
                "text": response_text
            }))

            # STEP 3: Text-to-Speech with ElevenLabs
            print("🔊 Generating speech with ElevenLabs...")
            audio_base64 = elevenlabs_service.text_to_speech_base64(response_text)

            # Convert base64 to bytes
            import base64
            audio_bytes = base64.b64decode(audio_base64)
            print(f"✅ Generated {len(audio_bytes)} bytes of MP3 audio")

            # Send audio to client
            await websocket.send(audio_bytes)
            print("🎉 Audio sent to client!")

        finally:
            # Clean up temp files
            import os
            if os.path.exists(temp_webm_path):
                os.unlink(temp_webm_path)
            if 'temp_wav_path' in locals() and os.path.exists(temp_wav_path):
                os.unlink(temp_wav_path)

    except Exception as e:
        print(f"❌ Error processing audio: {e}")
        import traceback
        traceback.print_exc()

async def handle_client(websocket):
    """Handle a client connection"""
    client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
    active_connections.add(websocket)
    audio_buffers[client_id] = []
    last_audio_time[client_id] = asyncio.get_event_loop().time()

    print(f"📞 Client connected: {client_id}")
    print(f"   Active connections: {len(active_connections)}")

    try:
        # Process audio chunks and accumulate for STT
        async for message in websocket:
            if isinstance(message, bytes):
                # Audio data received
                audio_size = len(message)
                current_time = asyncio.get_event_loop().time()

                # Add to buffer
                audio_buffers[client_id].append(message)
                last_audio_time[client_id] = current_time

                # Print progress
                total_chunks = len(audio_buffers[client_id])
                if total_chunks % 10 == 0:  # Every 10 chunks (~1 second)
                    print(f"🎵 Buffering audio: {total_chunks} chunks ({sum(len(c) for c in audio_buffers[client_id])} bytes)")

                # Process after 3 seconds of continuous audio
                if total_chunks >= 30:  # 30 chunks = ~3 seconds
                    print(f"\n📊 Buffer full, processing...")
                    await process_audio_buffer(client_id, websocket)
            else:
                # Text message received
                try:
                    data = json.loads(message)
                    print(f"📝 Text message from {client_id}: {data}")

                    # Send acknowledgment
                    await websocket.send(json.dumps({
                        "type": "ack",
                        "message": "Message received"
                    }))
                except json.JSONDecodeError:
                    print(f"⚠️  Invalid JSON from {client_id}")

    except websockets.exceptions.ConnectionClosed:
        print(f"📞 Client disconnected: {client_id}")
    except Exception as e:
        print(f"❌ Error handling client {client_id}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        active_connections.remove(websocket)
        print(f"   Active connections: {len(active_connections)}")

async def main():
    """Start the WebSocket server"""
    print("\n" + "="*60)
    print("🎤 HiRA VOICE TEST SERVER")
    print("="*60)
    print(f"Host: {HOST}")
    print(f"Port: {PORT}")
    print(f"WebSocket URL: ws://{HOST}:{PORT}")
    print(f"Services Available: {SERVICES_AVAILABLE}")
    print("="*60 + "\n")

    async with serve(handle_client, HOST, PORT):
        print("✅ Server started! Waiting for connections...\n")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        import traceback
        traceback.print_exc()
