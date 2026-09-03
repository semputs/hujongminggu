import os
import time
import requests
from google import genai
from google.genai import types

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Set http_options timeout to allow longer generation windows
client = genai.Client(
    api_key=GEMINI_KEY,
    http_options=types.HttpOptions(timeout=120000) # 120-second timeout
)

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    resp = requests.post(url, json=payload)
    resp.raise_for_status()

def discover_fresh_spots():
    prompt = """
    You are an expert local family outing curator for Kuala Lumpur.
    
    Recommend 1 specific, highly-rated family outing spot or cafe in or near:
    - Taman Melawati
    - Wangsa Maju
    - Setapak
    - Ampang

    Family & Design Requirements:
    1. Aesthetic: Japandi, warm oak, or clean minimalist decor.
    2. Kid/Family Friendly: Stroller accessible, high chairs, or play/open area for active toddlers.
    3. Comfort: Spacious and relaxed atmosphere.

    Return the response formatted as:
    📍 **[Venue Name]** - [Area/Neighborhood]
    ⭐ **Match Details:**
    • **Aesthetic:** [Design highlight]
    • **Kid Logistics:** [Stroller/kids facilities]
    • **Vibe & Tip:** [Best time to visit]
    """

    print("Generating recommendation with Gemini 3.6 Flash...")
    
    # Retry mechanism for network drops
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt == 2:
                raise e
            time.sleep(3)

if __name__ == "__main__":
    report = discover_fresh_spots()
    message = f"☕ **Weekend Spot Recommendation** 🎈\n\n{report}"
    send_telegram_message(message)
    print("Recommendation successfully sent to Telegram!")
    
