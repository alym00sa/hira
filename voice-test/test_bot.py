"""
Test Bot Creation Script
Creates a Recall.ai bot with output_media pointing to the voice test client
"""
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="../backend/.env")

# Configuration
RECALL_API_KEY = os.getenv("RECALL_API_KEY", "45cb49af128deb00d9883c41cc0701afb4b65824")
RECALL_REGION = "us-west-2"
API_BASE = f"https://{RECALL_REGION}.recall.ai/api/v1"

# Headers
HEADERS = {
    "Authorization": f"Token {RECALL_API_KEY}",
    "Content-Type": "application/json"
}

def create_voice_bot(meeting_url: str, client_url: str, ws_url: str, bot_name: str = "HiRA Voice Test"):
    """
    Create a bot with output_media configuration

    Args:
        meeting_url: Zoom/Meet meeting URL
        client_url: Public URL to your deployed client page (e.g., https://your-app.netlify.app)
        ws_url: Public WebSocket URL (e.g., wss://abc123.ngrok-free.app)
        bot_name: Name for the bot

    Returns:
        Bot creation response
    """
    # Build the full client URL with WebSocket parameter
    full_client_url = f"{client_url}?ws={ws_url}"

    payload = {
        "meeting_url": meeting_url,
        "bot_name": bot_name,
        "output_media": {
            "camera": {
                "kind": "webpage",
                "config": {
                    "url": full_client_url
                }
            }
        },
        "variant": {
            "zoom": "web_4_core",
            "google_meet": "web_4_core",
            "microsoft_teams": "web_4_core"
        }
    }

    print("\n" + "="*60)
    print("🤖 CREATING VOICE BOT")
    print("="*60)
    print(f"Meeting URL: {meeting_url}")
    print(f"Bot Name: {bot_name}")
    print(f"Client URL: {full_client_url}")
    print(f"WebSocket URL: {ws_url}")
    print("="*60 + "\n")

    try:
        response = requests.post(
            f"{API_BASE}/bot/",
            headers=HEADERS,
            json=payload,
            timeout=30
        )
        response.raise_for_status()

        bot_data = response.json()
        bot_id = bot_data.get("id")

        print("✅ Bot created successfully!")
        print(f"   Bot ID: {bot_id}")
        print(f"\n📺 The bot will join and display your client page")
        print(f"   The webpage's audio will play in the meeting")
        print(f"\n💡 Next steps:")
        print(f"   1. Wait for bot to join the meeting")
        print(f"   2. Check if you can see the HiRA interface")
        print(f"   3. Speak to test audio capture")
        print(f"   4. Check server.py logs for audio reception\n")

        return {
            "success": True,
            "bot_id": bot_id,
            "client_url": full_client_url
        }

    except requests.exceptions.HTTPError as e:
        print(f"❌ Failed to create bot: {e}")
        print(f"   Response: {e.response.text}")
        return {
            "success": False,
            "error": str(e),
            "response": e.response.text
        }

if __name__ == "__main__":
    print("\n🎤 HiRA Voice Bot Creator\n")

    # Get input from user
    meeting_url = input("Enter meeting URL: ").strip()

    print("\n📝 You need to deploy the client first!")
    print("   Options:")
    print("   1. Deploy client/ folder to Netlify/Vercel")
    print("   2. Or use ngrok: 'cd client && python -m http.server 8000' then 'ngrok http 8000'")
    print("")

    client_url = input("Enter deployed client URL (e.g., https://your-app.netlify.app): ").strip()

    print("\n🔌 You need to expose your WebSocket server!")
    print("   Run: ngrok http 8765")
    print("   Then use the HTTPS URL it gives you (replace https:// with wss://)")
    print("")

    ws_url = input("Enter WebSocket URL (e.g., wss://abc123.ngrok-free.app): ").strip()

    bot_name = input("Enter bot name (default: HiRA Voice Test): ").strip() or "HiRA Voice Test"

    # Create the bot
    result = create_voice_bot(meeting_url, client_url, ws_url, bot_name)

    if result["success"]:
        print("\n✨ Bot is joining the meeting!")
    else:
        print("\n❌ Bot creation failed. Check the error above.")
