import { useState, useEffect, useRef, useCallback } from 'react'
import { Mic, MicOff, Radio, AlertCircle, Loader2 } from 'lucide-react'
import '../styles/VoicePage.css'

// This page is displayed as the bot's video feed in Zoom meetings
// It connects to the relay server and handles voice interactions

function VoicePage() {
  // Get relay server URL from environment or use default
  const RELAY_SERVER_URL = import.meta.env.VITE_RELAY_URL || 'ws://localhost:8765'

  const [connectionStatus, setConnectionStatus] = useState('connecting')
  const [isListening, setIsListening] = useState(false)
  const [isThinking, setIsThinking] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [error, setError] = useState(null)
  const [lastTranscript, setLastTranscript] = useState('')

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

      // Handle transcript
      client.on('conversation.item.input_audio_transcription.completed', ({ transcript }) => {
        setLastTranscript(transcript)
      })

      // Start recording
      await wavRecorder.record((data) => client.appendInputAudio(data.mono))

      // Send initial greeting
      client.sendUserMessageContent([
        {
          type: 'input_text',
          text: 'Hello! I am ready to help.'
        }
      ])

    } catch (err) {
      console.error('Connection failed:', err)
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

  const getStatusColor = () => {
    if (error || connectionStatus === 'error') return 'error'
    if (isSpeaking) return 'speaking'
    if (isThinking) return 'thinking'
    if (isListening) return 'listening'
    if (connectionStatus === 'connected') return 'connected'
    return 'connecting'
  }

  const getStatusText = () => {
    if (error) return 'Connection Error'
    if (isSpeaking) return 'Speaking...'
    if (isThinking) return 'Thinking...'
    if (isListening) return 'Listening...'
    if (connectionStatus === 'connected') return 'Ready'
    if (connectionStatus === 'connecting') return 'Connecting...'
    return 'Disconnected'
  }

  const getStatusIcon = () => {
    if (error || connectionStatus === 'error') {
      return <AlertCircle size={32} />
    }
    if (isSpeaking || isListening) {
      return <Mic size={32} />
    }
    if (isThinking) {
      return <Loader2 size={32} className="spinner" />
    }
    if (connectionStatus === 'connected') {
      return <Radio size={32} />
    }
    return <MicOff size={32} />
  }

  return (
    <div className="voice-page">
      <div className="voice-container">
        {/* HiRA Branding */}
        <div className="voice-brand">
          <div className="brand-icon">
            <Radio size={48} />
          </div>
          <h1>HiRA</h1>
          <p>Human Rights Assistant</p>
        </div>

        {/* Status Indicator */}
        <div className={`voice-status status-${getStatusColor()}`}>
          <div className="status-icon">
            {getStatusIcon()}
          </div>
          <div className="status-text">{getStatusText()}</div>
        </div>

        {/* Visual Feedback */}
        <div className="voice-visualizer">
          {(isListening || isSpeaking) && (
            <div className="audio-waves">
              <div className="wave"></div>
              <div className="wave"></div>
              <div className="wave"></div>
              <div className="wave"></div>
              <div className="wave"></div>
            </div>
          )}
          {isThinking && (
            <div className="thinking-dots">
              <div className="dot"></div>
              <div className="dot"></div>
              <div className="dot"></div>
            </div>
          )}
        </div>

        {/* Last Transcript */}
        {lastTranscript && (
          <div className="voice-transcript">
            <div className="transcript-label">You said:</div>
            <div className="transcript-text">"{lastTranscript}"</div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="voice-error">
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        )}

        {/* Instructions */}
        <div className="voice-instructions">
          <h3>How to interact with HiRA:</h3>
          <ul>
            <li>Say <strong>"Hey HiRA"</strong> followed by your question</li>
            <li>HiRA will search the knowledge base and respond</li>
            <li>You can also message <strong>@HiRA</strong> in chat</li>
          </ul>
        </div>

        {/* Connection Info */}
        <div className="voice-footer">
          <div className="connection-info">
            <div className={`connection-dot status-${getStatusColor()}`}></div>
            <span>{RELAY_SERVER_URL}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

export default VoicePage
