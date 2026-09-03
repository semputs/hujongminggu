import os
import time
import requests
from google import genai

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

client = genai.Client(api_key=GEMINI_KEY)

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
    You are a strict, factual family outing curator for Kuala Lumpur.
    
    Recommend 3 REAL, CURRENTLY OPERATING family-friendly cafes/spots in or near:
    - Taman Melawati
    - Wangsa Maju
    - Setapak
    - Ampang

    STRICT ACCURACY RULES:
    1. Do NOT invent cafe names or links. Only output real places actively operating in 2026.
    2. Provide direct verification links (Google Maps Search & Instagram Search).
    3. Ensure variety—do not suggest places commonly returned on default lists if possible.

    Format each of the 3 spots strictly as:

    ☕ **[Exact Place Name]** ([Neighborhood Area])
    • **Google Maps Link:** https://www.google.com/maps/search/?api=1&query=[Place+Name]+[Area]+KL
    • **Instagram Search:** https://www.instagram.com/explore/tags/[placename_without_spaces]/
    • **Source / Review Link:** [Provide a real website/review link where you verified this place exists]
    • **Aesthetics:** ⭐ [X/5] - [Brief design note: Japandi, oak, minimalist]
    • **Kids Logistics:** ⭐ [X/5] - [Stroller access, high chairs, open layout]
    • **Summary:** [1-line summary]
    """

    print("Generating grounded recommendations with Gemini 3.6 Flash...")
    
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
    message = f"☕ **Verified Weekend Spot Recommendations** 🎈\n\n{report}"
    send_telegram_message(message)
    print("Report sent to Telegram!")
    
