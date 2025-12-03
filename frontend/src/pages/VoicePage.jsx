import { useState, useEffect, useRef, useCallback } from 'react'
import '../styles/VoicePage.css'

function VoicePage() {
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'
  const OPENAI_API_KEY = import.meta.env.VITE_OPENAI_API_KEY

  const [connectionStatus, setConnectionStatus] = useState('connecting')
  const [isListening, setIsListening] = useState(false)
  const [isThinking, setIsThinking] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [error, setError] = useState(null)

  const clientRef = useRef(null)
  const wavRecorderRef = useRef(null)
  const wavStreamPlayerRef = useRef(null)
  const isConnectedRef = useRef(false)

  // HiRA tools for RAG
  const HIRA_TOOLS = [{
    type: "function",
    name: "search_knowledge_base",
    description: "Search the human rights knowledge base for information about HRBA, AI ethics, and related topics.",
    parameters: {
      type: "object",
      properties: {
        query: { type: "string", description: "The search query" }
      },
      required: ["query"]
    }
  }]

  const HIRA_INSTRUCTIONS = `You are HiRA (Human Rights Assistant), a voice AI specializing in human rights-based approaches.

CRITICAL WAKE WORD RULE: ONLY respond when you hear "Hey HiRA" at the START of speech. Stay silent otherwise.

When someone says "Hey HiRA" followed by their question:
1. Use search_knowledge_base to find information
2. Give a BRIEF, conversational response (2-3 sentences for voice)
3. Mention a source if helpful`

  const connectToOpenAI = useCallback(async () => {
    if (isConnectedRef.current) return

    if (!OPENAI_API_KEY) {
      setError('OpenAI API key not configured')
      setConnectionStatus('error')
      return
    }

    try {
      setConnectionStatus('connecting')
      setError(null)

      // Dynamically import OpenAI Realtime SDK
      const { RealtimeClient } = await import('@openai/realtime-api-beta')
      const { WavRecorder, WavStreamPlayer } = await import('../lib/wavtools/index.js')

      // Initialize audio components
      if (!clientRef.current) {
        clientRef.current = new RealtimeClient({
          apiKey: OPENAI_API_KEY,
          dangerouslyAllowAPIKeyInBrowser: true
        })
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
      console.log('🎤 Requesting microphone access...')
      await wavRecorder.begin()
      console.log('✅ Microphone connected')

      // Connect to audio output
      console.log('🔊 Connecting audio output...')
      await wavStreamPlayer.connect()
      console.log('✅ Audio output connected')

      // Connect to OpenAI Realtime API
      console.log('🔌 Connecting to OpenAI...')
      await client.connect()
      console.log('✅ OpenAI connected')

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

      // Update session with tools and instructions
      client.updateSession({
        turn_detection: { type: 'server_vad' },
        tools: HIRA_TOOLS,
        tool_choice: 'auto',
        voice: 'shimmer',
        instructions: HIRA_INSTRUCTIONS,
        temperature: 0.7
      })

      // Handle function calls
      client.on('conversation.updated', async ({ item, delta }) => {
        // Handle audio deltas
        if (delta?.audio) {
          wavStreamPlayer.add16BitPCM(delta.audio, item.id)
          setIsSpeaking(true)
        }

        // Handle function calls
        if (item.type === 'function_call' && item.status === 'completed') {
          if (item.name === 'search_knowledge_base') {
            try {
              const args = JSON.parse(item.arguments)
              console.log('🔍 Searching knowledge base:', args.query)

              // Call our Railway backend for RAG
              const response = await fetch(`${API_BASE_URL}/rag/search`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: args.query, n_results: 3 })
              })

              if (!response.ok) {
                throw new Error('RAG search failed')
              }

              const result = await response.json()
              console.log('✅ RAG result:', result)

              // Send function result back to OpenAI
              client.sendFunctionCallOutput(item.call_id, result)
            } catch (error) {
              console.error('❌ RAG error:', error)
              client.sendFunctionCallOutput(item.call_id, {
                error: 'Failed to search knowledge base'
              })
            }
          }
        }

        // Handle completed items
        if (item.status === 'completed' && item.formatted?.audio?.length) {
          setIsSpeaking(false)
          setIsThinking(false)

          const wavFile = await WavRecorder.decode(
            item.formatted.audio,
            24000,
            24000
          )
          item.formatted.file = wavFile
        }
      })

      // Handle speech detection with debounce
      let speechTimeout = null
      client.on('input_audio_buffer.speech_started', () => {
        speechTimeout = setTimeout(() => {
          setIsListening(true)
        }, 200)
      })

      client.on('input_audio_buffer.speech_stopped', () => {
        if (speechTimeout) clearTimeout(speechTimeout)
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
      console.log('🎙️ Starting microphone recording...')
      await wavRecorder.record((data) => {
        console.log('🎤 Audio data structure:', data)
        const audioData = data.mono || data
        console.log('🎤 Audio chunk received:', audioData?.length || 'unknown', 'samples')
        client.appendInputAudio(audioData)
      })
      console.log('✅ Recording started')

      console.log('✅ Connected to OpenAI Realtime API (direct connection)')

    } catch (err) {
      console.error('❌ Connection failed:', err)
      setError(err.message || 'Failed to connect')
      setConnectionStatus('error')
      isConnectedRef.current = false
    }
  }, [API_BASE_URL, OPENAI_API_KEY])

  useEffect(() => {
    connectToOpenAI()

    return () => {
      // Cleanup on unmount
      if (clientRef.current) {
        clientRef.current.disconnect()
      }
      if (wavRecorderRef.current) {
        wavRecorderRef.current.end()
      }
    }
  }, [connectToOpenAI])

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
