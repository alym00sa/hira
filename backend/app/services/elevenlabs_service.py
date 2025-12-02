"""
ElevenLabs service for text-to-speech in meetings
"""
import requests
import base64
from app.core.config import settings

class ElevenLabsService:
    """Service for generating speech audio using ElevenLabs"""

    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        self.base_url = "https://api.elevenlabs.io/v1"

        # Use a professional, warm female voice (Rachel)
        # You can change this to any ElevenLabs voice ID
        self.voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel - warm, professional

    def text_to_speech(self, text: str) -> bytes:
        """
        Convert text to speech audio

        Args:
            text: Text to convert to speech

        Returns:
            Audio bytes (MP3 format)
        """
        url = f"{self.base_url}/text-to-speech/{self.voice_id}"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }

        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.5,
                "use_speaker_boost": True
            }
        }

        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()

            audio_bytes = response.content
            print(f"✅ Generated {len(audio_bytes)} bytes of speech")
            return audio_bytes

        except requests.exceptions.RequestException as e:
            print(f"❌ ElevenLabs TTS error: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Response: {e.response.text}")
            raise

    def text_to_speech_base64(self, text: str) -> str:
        """
        Convert text to speech and return as base64 string

        Args:
            text: Text to convert to speech

        Returns:
            Base64 encoded audio (MP3)
        """
        audio_bytes = self.text_to_speech(text)
        return base64.b64encode(audio_bytes).decode('utf-8')

# Singleton instance
elevenlabs_service = ElevenLabsService()
