"""
Deepgram service for real-time speech-to-text transcription
"""
import asyncio
import json
from typing import Optional, Callable
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from app.core.config import settings

class DeepgramService:
    """Service for real-time audio transcription using Deepgram"""

    def __init__(self):
        self.api_key = settings.DEEPGRAM_API_KEY
        self.client = None
        self.connection = None
        self.transcript_buffer = []

    async def start_transcription(self, on_transcript: Callable[[str], None]):
        """
        Start real-time transcription

        Args:
            on_transcript: Callback function called with each transcript segment
        """
        try:
            # Initialize Deepgram client
            self.client = DeepgramClient(self.api_key)

            # Create connection
            self.connection = self.client.listen.asyncwebsocket.v("1")

            # Set up event handlers
            async def on_message(self, result, **kwargs):
                sentence = result.channel.alternatives[0].transcript

                if len(sentence) > 0:
                    # Call the callback with the transcript
                    if on_transcript:
                        on_transcript(sentence)

                    # Also store in buffer
                    self.transcript_buffer.append(sentence)
                    print(f"🎤 Transcript: {sentence}")

            async def on_error(self, error, **kwargs):
                print(f"❌ Deepgram error: {error}")

            # Register handlers
            self.connection.on(LiveTranscriptionEvents.Transcript, on_message)
            self.connection.on(LiveTranscriptionEvents.Error, on_error)

            # Configure transcription options
            options = LiveOptions(
                model="nova-2",
                language="en-US",
                smart_format=True,
                interim_results=False,  # Only get final results
                punctuate=True,
                diarize=True,  # Speaker diarization
                encoding="linear16",
                sample_rate=16000,
                channels=1
            )

            # Start connection
            await self.connection.start(options)
            print("✅ Deepgram transcription started")

        except Exception as e:
            print(f"❌ Failed to start Deepgram: {str(e)}")
            raise

    async def send_audio(self, audio_data: bytes):
        """
        Send audio data for transcription

        Args:
            audio_data: Raw audio bytes (PCM16, 16kHz, mono)
        """
        if self.connection:
            try:
                await self.connection.send(audio_data)
            except Exception as e:
                print(f"❌ Error sending audio to Deepgram: {str(e)}")

    async def stop_transcription(self) -> str:
        """
        Stop transcription and return full transcript

        Returns:
            Complete transcript as a single string
        """
        if self.connection:
            try:
                await self.connection.finish()
                print("✅ Deepgram transcription stopped")
            except Exception as e:
                print(f"❌ Error stopping Deepgram: {str(e)}")

        # Return full transcript
        full_transcript = " ".join(self.transcript_buffer)
        self.transcript_buffer = []
        return full_transcript

    def get_current_transcript(self) -> str:
        """Get current transcript buffer as string"""
        return " ".join(self.transcript_buffer)
