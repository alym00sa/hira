"""
Recall.ai service for Zoom meeting bot integration
"""
import requests
from typing import Optional, Dict
from app.core.config import settings

class RecallService:
    """Service for interacting with Recall.ai API"""

    def __init__(self):
        self.base_url = "https://us-west-2.recall.ai/api/v1"
        self.api_key = settings.RECALL_API_KEY
        print(f"🔑 Recall API Key loaded: {self.api_key[:10]}..." if self.api_key else "⚠️ No API key found!")
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Token {self.api_key}"  # Recall.ai requires "Token" prefix
        }
        self.bot_id: Optional[str] = None

    def create_bot(self, meeting_url: str, bot_name: str = "HiRA", output_media: Optional[str] = None) -> Dict:
        """
        Create a bot and join it to a Zoom meeting

        Args:
            meeting_url: Zoom meeting URL
            bot_name: Name the bot will appear as in the meeting
            output_media: Optional URL to display as bot's video feed (for voice interface)

        Returns:
            Bot creation response with bot_id
        """
        # Get webhook URL from settings
        webhook_url = settings.WEBHOOK_URL

        # Configure webhook endpoints (new API format)
        endpoints = [
            {
                "type": "webhook",
                "url": f"{webhook_url}/api/v1/bot/chat-webhook",  # Chat events
                "events": [
                    "participant_events.chat_message",
                    "participant_events.join",
                    "participant_events.leave"
                ]
            },
            {
                "type": "webhook",
                "url": f"{webhook_url}/api/v1/bot/transcript-webhook",  # Transcript events
                "events": [
                    "transcript.data"  # Only finalized transcripts (prevents duplicates)
                ]
            }
        ]

        # Recording config (new API format)
        recording_config = {
            "transcript": {
                "provider": {
                    "recallai_streaming": {
                        "language_code": "en",
                        "mode": "prioritize_low_latency"
                    }
                }
            },
            "participant_events": {},
            "meeting_metadata": {},
            "realtime_endpoints": endpoints,
            "start_recording_on": "participant_join"
        }

        payload = {
            "meeting_url": meeting_url,
            "bot_name": bot_name,
            "bot_image": "web_gpu",  # Best performance with GPU for smooth video streaming ($1.70/hour)
            "recording_config": recording_config
        }

        # Add output_media if provided (for voice interface)
        if output_media:
            payload["output_media"] = {
                "camera": {
                    "kind": "webpage",
                    "config": {
                        "url": output_media
                    }
                }
            }
            print(f"🎥 Voice interface enabled: {output_media}")

        try:
            url = f"{self.base_url}/bot/"  # Match working test format
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            self.bot_id = data.get('id')

            print(f"✅ Recall.ai bot created: {self.bot_id}")
            print(f"   Bot name: {bot_name}")
            print(f"   Meeting URL: {meeting_url}")

            return data
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to create bot: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Response: {e.response.text}")
            raise

    def get_bot_status(self, bot_id: Optional[str] = None) -> Dict:
        """
        Get current bot status

        Args:
            bot_id: Bot ID (uses self.bot_id if not provided)

        Returns:
            Bot status information
        """
        bot_id = bot_id or self.bot_id
        if not bot_id:
            raise ValueError("No bot_id provided")

        url = f"{self.base_url}/bot/{bot_id}"  # Add /bot/ prefix for consistency

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to get bot status: {str(e)}")
            raise

    def leave_meeting(self, bot_id: Optional[str] = None) -> Dict:
        """
        Make the bot leave the meeting

        Args:
            bot_id: Bot ID (uses self.bot_id if not provided)

        Returns:
            Leave call response
        """
        bot_id = bot_id or self.bot_id
        if not bot_id:
            raise ValueError("No bot_id provided")

        url = f"{self.base_url}/bot/{bot_id}/leave_call"  # Add /bot/ prefix for consistency

        try:
            response = requests.post(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            print(f"✅ Bot {bot_id} left the meeting")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to leave meeting: {str(e)}")
            raise

    def send_chat_message(self, message: str, bot_id: Optional[str] = None) -> Dict:
        """
        Send a chat message in the meeting

        Args:
            message: Message text to send
            bot_id: Bot ID (uses self.bot_id if not provided)

        Returns:
            Send message response
        """
        bot_id = bot_id or self.bot_id
        if not bot_id:
            raise ValueError("No bot_id provided")

        url = f"{self.base_url}/bot/{bot_id}/send_chat_message/"
        payload = {"message": message, "send_to": "everyone"}

        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to send chat message: {str(e)}")
            raise

    def output_audio(self, audio_base64: str, bot_id: Optional[str] = None) -> Dict:
        """
        Play audio in the meeting

        Args:
            audio_base64: Base64 encoded audio (MP3 format)
            bot_id: Bot ID (uses self.bot_id if not provided)

        Returns:
            Output audio response
        """
        bot_id = bot_id or self.bot_id
        if not bot_id:
            raise ValueError("No bot_id provided")

        url = f"{self.base_url}/bot/{bot_id}/output_audio/"  # Match working test format
        payload = {
            "b64_data": audio_base64,
            "kind": "mp3"
        }

        try:
            print(f"🔊 Sending audio to meeting ({len(audio_base64)} chars)")
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            print(f"✅ Audio sent successfully")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to output audio: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Response: {e.response.text}")
            raise

# Singleton instance
recall_service = RecallService()
