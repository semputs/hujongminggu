import os
import time
import requests
from google import genai
from google.genai import types

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Reduced timeout to 30s so it retries fast instead of hanging
client = genai.Client(
    api_key=GEMINI_KEY,
    http_options=types.HttpOptions(timeout=30000)
)

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": False
    }
    resp = requests.post(url, json=payload)
    print(f"Telegram API Status: {resp.status_code}")
    resp.raise_for_status()

def discover_fresh_spots():
    prompt = """
    You are an expert family outing curator for Kuala Lumpur.
    
    Recommend 3 distinct family-friendly cafes/spots near Melawati, Wangsa Maju, Setapak, or Ampang.
    
    Criteria:
    - Japandi/warm oak/minimalist aesthetic
    - Stroller access/high chairs/kids space
    - Not overly cramped

    Format for each spot:
    ☕ [Venue Name] ([Area])
    • Google Maps: [Insert Search/Maps URL]
    • Instagram: @[handle] (https://instagram.com/[handle])
    • Aesthetics: ⭐ [X/5] - [Brief note]
    • Kids Logistics: ⭐ [X/5] - [Brief note]
    • Summary: [1-line summary]
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
            time.sleep(1) # Fast 1-second retry pause

if __name__ == "__main__":
    report = discover_fresh_spots()
    message = f"☕ **Top 3 Weekend Spot Recommendations** 🎈\n\n{report}"
    send_telegram_message(message)
    print("3 Recommendations successfully sent to Telegram!")
    
