import { useState, useEffect, useRef, useCallback } from 'react'
import '../styles/VoicePage.css'

function VoicePage() {
  // Get relay server URL from environment or use default
  const RELAY_SERVER_URL = import.meta.env.VITE_RELAY_URL || 'ws://localhost:8765'

  const [connectionStatus, setConnectionStatus] = useState('connecting')
  const [isListening, setIsListening] = useState(false)
  const [isThinking, setIsThinking] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [error, setError] = useState(null)

  const clientRef = useRef(null)
  const wavRecorderRef = useRef(null)
  const wavStreamPlayerRef = useRef(null)
  const isConnectedRef = useRef(false)

  const connectToRelay = useCallback(async () => {
    if (isConnectedRef.current) return

    try {
      setConnectionStatus('connecting')
      setError(null)

      // Dynamically import OpenAI Realtime SDK
      const { RealtimeClient } = await import('@openai/realtime-api-beta')
      const { WavRecorder, WavStreamPlayer } = await import('../lib/wavtools/index.js')

      // Initialize audio components
      if (!clientRef.current) {
        clientRef.current = new RealtimeClient({ url: RELAY_SERVER_URL })
      }
      if (!wavRecorderRef.current) {
        wavRecorderRef.current = new WavRecorder({ sampleRate: 24000 })
      }
      if (!wavStreamPlayerRef.current) {
        wavStreamPlayerRef.current = new WavStreamPlayer({ sampleRate: 24000 })
      }

      const client = clientRef.current
      const wavRecorder = wavRecorderRef.current
      const wavStreamPlayer = wavStreamPlayerRef.current

      // Connect to microphone
      await wavRecorder.begin()

      // Connect to audio output
      await wavStreamPlayer.connect()

      // Connect to relay server
      await client.connect()

      isConnectedRef.current = true
      setConnectionStatus('connected')

      // Set up event handlers
      client.on('error', (event) => {
        console.error('Realtime error:', event)
        setError('Connection error')
        setConnectionStatus('error')
      })

      client.on('disconnected', () => {
        isConnectedRef.current = false
        setConnectionStatus('disconnected')
      })

      // Update session with VAD
      client.updateSession({
        turn_detection: { type: 'server_vad' }
      })

      // Handle conversation updates
      client.on('conversation.updated', async ({ item, delta }) => {
        // Handle audio deltas
        if (delta?.audio) {
          wavStreamPlayer.add16BitPCM(delta.audio, item.id)
          setIsSpeaking(true)
        }

        // Handle completed items
        if (item.status === 'completed') {
          setIsSpeaking(false)
          setIsThinking(false)

          if (item.formatted.audio?.length) {
            const wavFile = await WavRecorder.decode(
              item.formatted.audio,
              24000,
              24000
            )
            item.formatted.file = wavFile
          }
        }
      })

      // Handle speech detection
      client.on('input_audio_buffer.speech_started', () => {
        setIsListening(true)
      })

      client.on('input_audio_buffer.speech_stopped', () => {
        setIsListening(false)
        setIsThinking(true)
      })

      // Handle conversation interruptions
      client.on('conversation.interrupted', async () => {
        const trackSampleOffset = await wavStreamPlayer.interrupt()
        if (trackSampleOffset?.trackId) {
          const { trackId, offset } = trackSampleOffset
          await client.cancelResponse(trackId, offset)
        }
        setIsSpeaking(false)
        setIsThinking(false)
      })

      // Start recording
      await wavRecorder.record((data) => client.appendInputAudio(data.mono))

      // No initial greeting - wait for "Hey HiRA" wake word

    } catch (err) {
      console.error('❌ Connection failed:', err)
      setError(err.message || 'Failed to connect')
      setConnectionStatus('error')
      isConnectedRef.current = false
    }
  }, [RELAY_SERVER_URL])

  useEffect(() => {
    connectToRelay()

    return () => {
      // Cleanup on unmount
      if (clientRef.current) {
        clientRef.current.disconnect()
      }
      if (wavRecorderRef.current) {
        wavRecorderRef.current.end()
      }
    }
  }, [connectToRelay])

  // Determine status for CSS class
  const getStatus = () => {
    if (error || connectionStatus === 'error') return 'error'
    if (isSpeaking) return 'speaking'
    if (isThinking) return 'thinking'
    if (isListening) return 'listening'
    if (connectionStatus === 'connected') return 'ready'
    return 'connecting'
  }

  return (
    <div className="voice-page">
      <div className="voice-content">
        <h1 className={`hira-title ${getStatus()}`}>HiRA</h1>
        {connectionStatus === 'connecting' && <p className="status-text">Connecting...</p>}
        {error && <p className="status-text error">{error}</p>}
      </div>
    </div>
  )
}

export default VoicePage
