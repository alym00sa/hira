# HiRA Voice Test Environment

Quick iteration environment for testing the voice pipeline before integrating into main HiRA app.

## Architecture

```
Client (HTML page)  ←→  WebSocket Server  ←→  Services (STT/LLM/TTS)
      ↓                        ↓                     ↓
  Audio I/O              Streaming Audio        Deepgram/ElevenLabs
```

## Quick Start

### 1. Start WebSocket Server

```bash
cd voice-test
python server.py
```

Server will start on `ws://localhost:8765`

### 2. Serve Client Page

Open `client/index.html` in a browser, OR serve it locally:

```bash
cd client
python -m http.server 8000
```

Then open: `http://localhost:8000`

### 3. Test Locally First

- Open client page in browser
- Allow microphone access
- Speak - you should see "Listening" status
- In echo mode, you'll hear yourself back

### 4. Deploy for Bot Testing

Once working locally:

**A. Deploy Client:**
- Upload `client/` folder to Netlify/Vercel/GitHub Pages
- Get public URL (e.g., `https://your-app.netlify.app`)

**B. Expose WebSocket:**
```bash
ngrok http 8765
```
Get WSS URL (e.g., `wss://abc123.ngrok-free.app`)

**C. Create Bot:**
Update `test_bot.py` with your URLs and run:
```bash
python test_bot.py
```

## Development Phases

### Phase 1: Echo Test ✅ (Current)
- [x] Client captures audio
- [x] WebSocket server receives audio
- [x] Server echoes audio back
- **Goal:** Verify audio pipeline works

### Phase 2: Add STT (Next)
- [ ] Integrate Deepgram for speech-to-text
- [ ] Display transcript in client
- **Goal:** Verify we can understand speech

### Phase 3: Add TTS
- [ ] Integrate ElevenLabs for text-to-speech
- [ ] Send synthesized audio back to client
- **Goal:** Verify bot can speak

### Phase 4: Add RAG + LLM
- [ ] Connect to RAG engine
- [ ] Generate intelligent responses
- [ ] Full conversation loop
- **Goal:** Complete voice interaction

### Phase 5: Integration
- [ ] Copy working code to main HiRA app
- [ ] Add `/bot-video` route to React frontend
- [ ] Update main backend with WebSocket endpoint

## Files

```
voice-test/
├── client/
│   └── index.html          # Bot video page (streamed to meeting)
├── server.py               # WebSocket server
├── test_bot.py             # Bot creation script
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Troubleshooting

**Client not connecting?**
- Check server is running on port 8765
- Check WebSocket URL in client (query param `?ws=...`)
- Check firewall settings

**No audio?**
- Check microphone permissions in browser
- Check browser console for errors
- Try a different browser (Chrome/Edge work best)

**Bot muted in Zoom?**
- This is expected with output_media approach
- The webpage's audio plays automatically
- No manual unmuting needed

## Next Steps

1. Test echo mode locally
2. Add STT integration
3. Add TTS integration
4. Add RAG + LLM
5. Deploy and test with actual bot
6. Integrate into main HiRA app
