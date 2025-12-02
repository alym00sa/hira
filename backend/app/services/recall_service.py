"""
Recall.ai service for Zoom meeting bot integration
"""
import requests
import os
from typing import Optional, Dict
from app.core.config import settings

class RecallService:
    """Service for interacting with Recall.ai API"""

    def __init__(self):
        self.base_url = "https://us-east-1.recall.ai/api/v1/bot"
        self.api_key = os.getenv('RECALL_API_KEY', '')
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": self.api_key
        }
        self.bot_id: Optional[str] = None

    def create_bot(self, meeting_url: str, bot_name: str = "HiRA") -> Dict:
        """
        Create a bot and join it to a Zoom meeting

        Args:
            meeting_url: Zoom meeting URL
            bot_name: Name the bot will appear as in the meeting

        Returns:
            Bot creation response with bot_id
        """
        # Get webhook URL (will be set when server starts)
        webhook_url = os.getenv('WEBHOOK_URL', 'http://localhost:8000')

        payload = {
            "meeting_url": meeting_url,
            "bot_name": bot_name,
            "real_time_media": {
                "websocket_audio_destination_url": f"{webhook_url.replace('http', 'ws')}/api/v1/bot/audio"
            },
            "automatic_leave": {
                "waiting_room_timeout": 600  # Leave after 10 min in waiting room
            },
            "transcription_options": {
                "provider": "none"  # We'll handle transcription with Deepgram
            }
        }

        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload)
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

        url = f"{self.base_url}/{bot_id}"

        try:
            response = requests.get(url, headers=self.headers)
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

        url = f"{self.base_url}/{bot_id}/leave_call"

        try:
            response = requests.post(url, headers=self.headers)
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

        url = f"{self.base_url}/{bot_id}/send_chat_message"
        payload = {"message": message}

        try:
            response = requests.post(url, headers=self.headers, json=payload)
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

        url = f"{self.base_url}/{bot_id}/output_audio"
        payload = {
            "b64_data": audio_base64,
            "kind": "mp3"
        }

        try:
            print(f"🔊 Sending audio to meeting ({len(audio_base64)} chars)")
            response = requests.post(url, headers=self.headers, json=payload)
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
