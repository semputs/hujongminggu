import os
import requests
from google import genai

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

client = genai.Client(api_key=GEMINI_KEY)

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    resp = requests.post(url, json=payload)
    resp.raise_for_status()

def discover_fresh_spots():
    # Enforce temporal constraints and verification rules
    prompt = """
    You are an up-to-date local family concierge in KL. Your job is to find a FRESH, TRENDING, or NEWLY OPENED venue in Melawati, Wangsa Maju, Setapak, or Ampang.

    RECENCY RULES:
    1. Only consider spots that have recent reviews or posts from the LAST 30-60 DAYS, or newly opened spots in 2025/2026.
    2. Exclude permanently closed venues or older 2021-2023 listicles.
    3. Verify that the location is actively operating.

    FAMILY & DESIGN CRITERIA:
    - Interior: Japandi, warm oak, or minimalist aesthetic.
    - Family Friendly: Ground-floor or ramp access for strollers, high chairs, or play areas.
    - Comfort: Not excessively cramped.

    OUTPUT FORMAT:
    📍 **[Venue Name]** - [Exact Area/Neighborhood]
    🗓️ **Recency Proof:** [Mention recent review date or opening timeframe]
    ⭐ **Match Details:**
    • **Aesthetic:** [Design elements]
    • **Kid Logistics:** [Stroller/play facilities]
    • **Vibe & Tip:** [Best time to go to beat crowds]
    """

    print("Running grounded search for recent spots...")
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
        config={
            "tools": [{"google_search": {}}]
        }
    )
    
    return response.text

if __name__ == "__main__":
    report = discover_fresh_spots()
    message = f"☕ **Fresh Weekend Spot Finding** 🎈\n\n{report}"
    send_telegram_message(message)
    print("Fresh recommendation sent to Telegram!")
    
