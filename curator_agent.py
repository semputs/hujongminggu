import os
import time
import requests
from google import genai
from google.genai import types

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

client = genai.Client(
    api_key=GEMINI_KEY,
    http_options=types.HttpOptions(timeout=120000)
)

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False  # Enables visual link previews in Telegram
    }
    resp = requests.post(url, json=payload)
    print(f"Telegram API Status: {resp.status_code}")
    resp.raise_for_status()

def discover_fresh_spots():
    prompt = """
    You are an expert local family outing curator for Kuala Lumpur.
    
    Recommend EXACTLY 3 distinct, highly-rated family outing spots or cafes in or near:
    - Taman Melawati
    - Wangsa Maju
    - Setapak
    - Ampang

    Requirements for each venue:
    1. Aesthetic: Japandi, warm oak, or clean minimalist decor.
    2. Kid/Family Friendly: Stroller accessible, high chairs, play corners, or open space for toddlers.
    3. Comfort: Spacious and relaxed atmosphere.

    Format the output strictly as a Markdown report containing 3 entries. For each entry, provide:
    
    ☕ **[Venue Name]** ([Area])
    • **Google Maps:** [Link to Google Maps URL]
    • **Instagram:** @[instagram_handle] (https://instagram.com/[instagram_handle])
    • **Aesthetics Rating:** ⭐ [X/5] - [Short reason]
    • **Kids Logistics Rating:** ⭐ [X/5] - [Short reason regarding strollers/kids space]
    • **Summary:** [A single 1-line summary sentence capturing why it's great for the weekend]

    ---
    Ensure real, accurate venue names located around Ampang, Wangsa Maju, Melawati, or Setapak (e.g., Mori Kohi, Botanica+Co at Bamboo Hills, Green Tomato Cafe, or VCR Ritchie).
    """

    print("Generating 3 recommendations with Gemini 3.6 Flash...")
    
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
    message = f"☕ **Top 3 Weekend Spot Recommendations** 🎈\n\n{report}"
    send_telegram_message(message)
    print("3 Recommendations successfully sent to Telegram!")
    
