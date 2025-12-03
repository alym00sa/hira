# HiRA Voice Test - Progress & Next Steps

## ✅ COMPLETED

### 1. Voice Test Environment Setup
- ✅ Created `voice-test/` folder with isolated test environment
- ✅ Built HTML client (`client/index.html`) with:
  - Microphone capture using MediaRecorder
  - WebSocket communication
  - Audio playback using Web Audio API
  - Visual status indicators
- ✅ Created WebSocket server (`server.py`) with:
  - Audio buffering (accumulates 3 seconds of audio)
  - Connection management
  - Real-time audio streaming

### 2. Audio Pipeline
- ✅ Added Deepgram STT integration (Speech-to-Text)
- ✅ Added ElevenLabs TTS integration (Text-to-Speech)
- ✅ Added audio format conversion (WebM → WAV)
  - Uses pydub library
  - Requires ffmpeg (NOW INSTALLED)
- ✅ Fixed file handling issues (proper temp file cleanup)
- ✅ Added helpful error messages

### 3. Dependencies
- ✅ `requirements.txt` updated with:
  - websockets==12.0
  - python-dotenv==1.0.0
  - pydub==0.25.1
- ✅ FFmpeg installed via winget (PATH updated - requires terminal restart)

### 4. Backend Integration
- ✅ Loads .env from backend folder (Deepgram + ElevenLabs API keys)
- ✅ Imports backend services (DeepgramService, ElevenLabs, LLM, RAG)

## 🔄 CURRENT STATE

**Status:** Ready to test full STT→TTS pipeline

**What works:**
- Audio capture from browser
- WebSocket communication
- Audio buffering (3 seconds)
- File format conversion setup
- Deepgram transcription (prerecorded API)
- ElevenLabs speech generation
- Audio playback in browser

## 🧪 HOW TO TEST (Next Session)

### 1. Restart Terminal
FFmpeg was just installed - you MUST restart your terminal/VS Code for PATH changes to take effect.

### 2. Start the Server
```bash
cd C:\Users\jadea\Downloads\hrba-agent\voice-test
python server.py
```

Expected output:
```
📦 Added to path: C:\Users\jadea\Downloads\hrba-agent\backend
🔑 Loaded .env from: C:\Users\jadea\Downloads\hrba-agent\backend\.env
   Deepgram key: 6dc462fd022e085ba811...
   ElevenLabs key: sk_95108c8ab6a4444e82...
✅ Services imported successfully
🎤 Deepgram, LLM, and RAG services initialized

============================================================
🎤 HiRA VOICE TEST SERVER
============================================================
Host: 0.0.0.0
Port: 8765
WebSocket URL: ws://0.0.0.0:8765
Services Available: True
============================================================

✅ Server started! Waiting for connections...
```

### 3. Open the Client
Open `client/index.html` in your browser (double-click the file)

Expected: Should see "HiRA Voice Agent" interface with pulsing avatar

### 4. Test Voice Pipeline
- Speak clearly for 3+ seconds
- Watch server console for:
  ```
  🎵 Buffering audio: 10 chunks (...)
  🎵 Buffering audio: 20 chunks (...)
  🎵 Buffering audio: 30 chunks (...)

  📊 Buffer full, processing...
  🎤 Processing 30 chunks (XXX bytes)
  🔄 Converting WebM to WAV...
  ✅ Converted to WAV
  🎤 Transcribing with Deepgram...
  📝 Transcript: "your speech here"
  💬 Response: "You said: your speech here"
  🔊 Generating speech with ElevenLabs...
  ✅ Generated XXX bytes of MP3 audio
  🎉 Audio sent to client!
  ```
- Hear the response in browser: "You said: [your text]"

## 📋 TODO - REMAINING WORK

### ⏭️ Next: Add RAG Integration
**Goal:** Replace "You said: [text]" with intelligent responses from RAG system

**Changes needed in `server.py`:**
```python
# Replace lines 95-97 (current simple response):
response_text = f"You said: {transcript}"

# With RAG-powered response:
from app.rag.rag_engine import RAGEngine
from app.services.llm_service import LLMService

rag_engine = RAGEngine()
llm_service = LLMService()

# Get context from RAG
rag_context = rag_engine.get_context(
    question=transcript,
    user_id="voice_test"
)

# Generate intelligent response
if rag_context:
    result = await llm_service.generate_response(
        user_message=transcript,
        context=rag_context
    )
    response_text = result["message"]
else:
    response_text = "I don't have information about that in my knowledge base."
```

**Also add concise response guidance:**
```python
enhanced_question = f"""{transcript}

[IMPORTANT: This is a voice response. Keep it:
- BRIEF: 2-3 sentences maximum (50-75 words)
- CONVERSATIONAL: Natural speaking tone
- CLEAR: Simple language
Think of speaking out loud in a meeting.]"""
```

### 📦 After RAG Works: Deploy with Recall.ai Bot

**Goal:** Get the voice system working in actual Zoom meetings

**Steps:**
1. Deploy client to Netlify/Vercel
   - Upload `client/` folder
   - Get public URL (e.g., https://hira-voice.netlify.app)

2. Expose WebSocket server with ngrok
   ```bash
   ngrok http 8765
   ```
   - Get wss:// URL (e.g., wss://abc123.ngrok-free.app)

3. Create bot with `test_bot.py`
   ```bash
   python test_bot.py
   ```
   - Enter meeting URL
   - Enter deployed client URL
   - Enter ngrok WebSocket URL
   - Bot joins meeting with your client page as video

4. Test in real Zoom meeting
   - Bot displays your client interface
   - Browser captures meeting audio
   - Pipeline processes and responds
   - Meeting participants hear the TTS audio

### 🔮 Final Step: Integrate into Main HiRA App

**Goal:** Move from isolated voice-test to production HiRA backend

**Changes needed:**
1. Add `/bot-video` route to React frontend
   - Copy client/index.html logic to React component
   - Connect to main backend WebSocket

2. Add WebSocket endpoint to main backend
   - `backend/app/api/routes/voice.py`
   - Handle audio streaming
   - Use existing RAG/LLM services

3. Update bot creation in main app
   - Use `output_media` instead of chat-only
   - Point to main app's /bot-video route

## 📝 NOTES

### Architecture Decisions
- **Why output_media instead of output_audio?**
  - `output_audio` API doesn't work (bot gets auto-muted in Zoom)
  - `output_media` streams a webpage into the meeting as video
  - Webpage's audio plays in the meeting (not muted)

- **Why WebM → WAV conversion?**
  - Browser MediaRecorder outputs WebM/Opus format
  - Deepgram API requires WAV/MP3/FLAC
  - Conversion needed in both local testing AND production

- **Why 3-second buffering?**
  - Ensures enough audio for meaningful transcription
  - Balance between latency and accuracy
  - Can be adjusted (30 chunks × 100ms = 3 seconds)

### API Keys Location
```
backend/.env:
- DEEPGRAM_API_KEY=6dc462fd022e085ba811d5fdef2d88ded7e1e228
- ELEVENLABS_API_KEY=sk_95108c8ab6a4444e828046096f2ed7a39472b3c3c6a002f6
```

### File Structure
```
hrba-agent/
├── voice-test/              # Isolated test environment
│   ├── server.py           # WebSocket server with STT/TTS
│   ├── client/
│   │   └── index.html      # Browser client with audio capture
│   ├── test_bot.py         # Recall.ai bot creator
│   ├── requirements.txt    # Python dependencies
│   └── PROGRESS.md         # This file
│
├── backend/                # Main HiRA backend
│   ├── .env               # API keys
│   ├── app/
│   │   ├── services/
│   │   │   ├── deepgram_service.py    # STT
│   │   │   ├── elevenlabs_service.py  # TTS
│   │   │   └── llm_service.py         # Claude
│   │   └── rag/
│   │       └── rag_engine.py          # RAG system
│   └── ...
```

## 🚨 TROUBLESHOOTING

### If "FFmpeg not found" error:
1. Check: `ffmpeg -version` in terminal
2. If not found, restart terminal/VS Code
3. If still not found, add to PATH manually or download portable version

### If audio conversion fails:
- Check ffmpeg is accessible: `where ffmpeg`
- Verify temp files are being created: Check `C:\Users\jadea\AppData\Local\Temp\`
- Look for detailed error in server logs

### If no audio plays in browser:
- Check browser console for errors (F12)
- Verify MP3 audio is being received (check Network tab)
- Ensure Web Audio API is supported (modern browsers only)

### If transcription is empty:
- Speak louder and clearer
- Check microphone permissions in browser
- Verify audio chunks are being sent (server logs show "Buffering audio")
- Reduce buffering threshold for testing (line 157: change 30 to 15)

## 🎯 SUCCESS CRITERIA

**Current Phase:** ✅ Full STT→TTS pipeline working
- You say something → hear "You said: [text]" back

**Next Phase:** RAG integration
- You ask a question → hear intelligent answer from knowledge base

**Final Phase:** Production deployment
- Bot joins real Zoom meetings
- Responds to questions with voice
- All participants can hear the bot

---

**Last Updated:** 2025-12-02
**Status:** Ready for testing after terminal restart
