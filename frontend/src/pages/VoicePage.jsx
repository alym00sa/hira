import { useEffect, useRef, useState } from 'react';
import '../styles/VoicePage.css';

export default function VoicePage() {
  const [status, setStatus] = useState('connecting'); // connecting, ready, listening, thinking, speaking
  const clientRef = useRef(null);

  // Get relay server URL from environment or use default
  const RELAY_SERVER_URL = import.meta.env.VITE_RELAY_URL || 'ws://localhost:8765'

  useEffect(() => {
    connectToRelay();
    return () => {
      if (clientRef.current) {
        clientRef.current.disconnect();
      }
    };
  }, []);

  const connectToRelay = async () => {
    try {
      const { RealtimeClient } = await import('@openai/realtime-api-beta');
      const { WavRecorder, WavStreamPlayer } = await import('../lib/wavtools/index.js');

      // Initialize audio
      const wavRecorder = new WavRecorder({ sampleRate: 24000 });
      const wavStreamPlayer = new WavStreamPlayer({ sampleRate: 24000 });

      // Create client
      const client = new RealtimeClient({ url: RELAY_SERVER_URL });
      clientRef.current = client;

      // Event handlers
      client.on('connected', () => {
        console.log('✅ Connected to relay');
        setStatus('ready');
      });

      client.on('disconnected', () => {
        console.log('🔌 Disconnected');
        setStatus('connecting');
      });

      client.on('conversation.updated', ({ item, delta }) => {
        if (item.status === 'in_progress') {
          if (item.role === 'user') {
            setStatus('listening');
          } else if (item.type === 'function_call') {
            setStatus('thinking');
          }
        } else if (item.status === 'completed' && item.role === 'assistant') {
          setStatus('ready');
        }
      });

      client.on('conversation.interrupted', () => {
        setStatus('ready');
      });

      // Audio output
      client.on('conversation.updated', async ({ item, delta }) => {
        if (delta?.audio) {
          wavStreamPlayer.add16BitPCM(delta.audio, item.id);
        }
        if (item.status === 'completed' && item.formatted.audio?.length) {
          const wavFile = await WavRecorder.decode(
            item.formatted.audio,
            24000,
            24000
          );
          wavStreamPlayer.add16BitPCM(wavFile.getChannelData(0), item.id);
        }
      });

      // Track audio playback
      wavStreamPlayer.on('playback_start', () => {
        setStatus('speaking');
      });

      wavStreamPlayer.on('playback_stop', () => {
        setStatus('ready');
      });

      // Connect
      await wavRecorder.begin();
      await wavStreamPlayer.connect();
      await client.connect();

      // Send initial session update
      client.updateSession({
        turn_detection: { type: 'server_vad' },
        input_audio_transcription: { model: 'whisper-1' }
      });

      // Start recording
      await wavRecorder.record((data) => {
        client.appendInputAudio(data.mono);
      });

    } catch (error) {
      console.error('❌ Connection failed:', error);
      setStatus('error');
    }
  };

  return (
    <div className="voice-page">
      <div className="voice-content">
        <h1 className={`hira-title ${status}`}>HiRA</h1>
        {status === 'connecting' && <p className="status-text">Connecting...</p>}
        {status === 'error' && <p className="status-text error">Connection failed</p>}
      </div>
    </div>
  );
}
