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
    http_options=types.HttpOptions(timeout=30000)
)

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    }
    resp = requests.post(url, json=payload)
    resp.raise_for_status()

def discover_fresh_spots():
    prompt = """
    You are a strictly accurate family outing curator for Kuala Lumpur.
    
    Provide 3 REAL, POPULAR, AND CURRENTLY OPERATING family-friendly cafes/spots located in:
    - Taman Melawati
    - Wangsa Maju
    - Setapak
    - Ampang

    STRICT RULES:
    - Recommend ONLY well-known, established venues that you are 100% certain exist and are open in 2026.
    - Do NOT invent web addresses or raw shortened links.
    
    Format each spot strictly as:

    ☕ **[Place Name]** ([Area])
    📍 Search on Google Maps: "[Place Name] [Area] KL"
    📸 Search on Instagram: #[PlaceNameWithoutSpaces]
    • **Aesthetics Rating:** ⭐ [X/5] - [Design note]
    • **Kids Logistics Rating:** ⭐ [X/5] - [Stroller/space note]
    • **Summary:** [1-line summary]
    """

    print("Generating verified recommendations with Gemini 3.6 Flash...")
    
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
            time.sleep(1)

if __name__ == "__main__":
    report = discover_fresh_spots()
    message = f"☕ **Weekend Spot Recommendations** 🎈\n\n{report}"
    send_telegram_message(message)
    print("Report sent to Telegram successfully!")
    
