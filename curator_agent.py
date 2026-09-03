import os
import time
import urllib.parse
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
        "disable_web_page_preview": True
    }
    resp = requests.post(url, json=payload)
    resp.raise_for_status()

def discover_fresh_spots():
    # Force Gemini to return simple structured text so Python can format working links
    prompt = """
    You are a strictly accurate family outing curator for Kuala Lumpur.
    
    Provide EXACTLY 3 REAL, CURRENTLY OPERATING family-friendly cafes in:
    - Taman Melawati
    - Wangsa Maju
    - Setapak
    - Ampang

    Requirements:
    1. Only recommend real places active in 2026.
    2. Format output strictly like this for each venue:

    NAME: [Exact Cafe Name]
    AREA: [Neighborhood Name]
    IG_HANDLE: [instagram_handle_without_@_or_hashtag]
    AESTHETICS: [X/5] - [Short design summary]
    KIDS_LOGISTICS: [X/5] - [Short stroller/kids summary]
    SUMMARY: [1-sentence summary]
    ---
    """

    print("Generating verified recommendations...")
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )
    
    # Parse output lines and build real, working URLs programmatically
    raw_text = response.text
    blocks = raw_text.split("---")
    
    formatted_spots = []
    for block in blocks:
        lines = [line.strip() for line in block.strip().split("\n") if line.strip()]
        data = {}
        for line in lines:
            if ":" in line:
                key, val = line.split(":", 1)
                data[key.strip()] = val.strip()
        
        if "NAME" in data and "AREA" in data:
            name = data["NAME"]
            area = data["AREA"]
            
            # Construct real, clickable Google Maps Search URL
            query = urllib.parse.quote(f"{name} {area} KL")
            maps_url = f"https://www.google.com/maps/search/?api=1&query={query}"
            
            ig = data.get("IG_HANDLE", "").replace("@", "").replace("#", "")
            ig_url = f"https://www.instagram.com/explore/tags/{ig}/" if ig else "N/A"
            
            formatted_spot = (
                f"☕ **{name}** ({area})\n"
                f"📍 [Open in Google Maps]({maps_url})\n"
                f"📸 [View on Instagram]({ig_url})\n"
                f"• **Aesthetics Rating:** ⭐ {data.get('AESTHETICS', 'N/A')}\n"
                f"• **Kids Logistics Rating:** ⭐ {data.get('KIDS_LOGISTICS', 'N/A')}\n"
                f"• **Summary:** {data.get('SUMMARY', '')}\n"
            )
            formatted_spots.append(formatted_spot)

    return "\n".join(formatted_spots[:3])

if __name__ == "__main__":
    report = discover_fresh_spots()
    message = f"☕ **Verified Weekend Spot Recommendations** 🎈\n\n{report}"
    send_telegram_message(message)
    print("Report sent to Telegram successfully!")
    
