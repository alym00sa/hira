# HiRA Voice Test

## Available Relay Servers

### 1. `relay.py` - Minimal Relay (Basic Testing)
Simple WebSocket relay to OpenAI Realtime API. No RAG, no wake word detection.

### 2. `relay_with_rag_fixed.py` - RAG Integration
Adds RAG knowledge base search via function calling. Tools persist across session updates.

### 3. `relay_with_hybrid_wakeword.py` - Production Ready ✨
**Full-featured relay server with:**
- ✅ Hybrid wake word detection ("Hey HiRA")
- ✅ Meeting transcript buffering (last 50 items)
- ✅ Meeting context awareness (sends recent context with queries)
- ✅ RAG knowledge base search
- ✅ Shimmer voice
- ✅ Function calling for search_knowledge_base

---

## Quick Start

### 1. Install Dependencies

```bash
cd server
pip install -r requirements.txt
```

Make sure you have a `.env` file with:
```
OPENAI_API_KEY=sk-proj-...
```

### 2. Start the Enhanced Relay Server

```bash
python relay_with_hybrid_wakeword.py
```

You should see:
```
📦 Backend path: C:\Users\...\hrba-agent\backend
✅ OpenAI API Key loaded: sk-proj-8HYkE_CKW...
✅ RAG engine initialized
🎤 HIRA VOICE - Hybrid Wake Word + RAG + Meeting Context
Features:
  - Shimmer voice
  - Hybrid wake word detection ('Hey HiRA')
  - Meeting transcript buffering
  - RAG knowledge base search
Starting server on ws://0.0.0.0:8765
```

### 3. Connect Client

Use the client from `voice-agent-demo/client`:

```bash
cd ../voice-agent-demo/client
npm run dev
```

Then open: `http://localhost:5173?wss=ws://localhost:8765`

### 4. Test Voice Interaction

1. Click "Connect" in the browser
2. Say: **"Hey HiRA, what is HRBA?"**
3. HiRA will:
   - Detect the wake word
   - Extract the question
   - Search the knowledge base
   - Respond with voice (using shimmer voice)

---

## Server Features Explained

### Hybrid Wake Word Detection
- Buffers all transcript in memory (last 50 items)
- Uses regex to detect "hey hira" / "hi hira" / "hello hira" (case-insensitive)
- Extracts question from text after wake word
- Logs detection: `🎤 WAKE WORD DETECTED! Question: ...`

### Meeting Context Awareness
- Maintains transcript buffer with timestamps
- Sends last 10 items as context with each query
- Helps HiRA understand ongoing discussion
- Context included in RAG function results

### Transcript Buffering
- Captures user speech transcripts
- Captures HiRA responses
- Stores with speaker labels and timestamps
- Full transcript available for meeting summaries

### RAG Integration
- Intercepts `response.function_call_arguments.done` events
- Calls backend RAG engine with query
- Returns top 3 results (truncated for voice)
- Includes meeting context with results

---

## Next Steps

1. ✅ Local testing complete
2. 🚀 Deploy client to Railway
3. 🚀 Deploy relay server to Railway
4. 🤖 Update backend bot.py for output_media
5. 📹 Test in real Zoom meeting via Recall.ai
