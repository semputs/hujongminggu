import os
import random
import urllib.parse
import requests
from google import genai

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
PLACES_KEY = os.environ.get("PLACES_API_KEY")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

client = genai.Client(api_key=GEMINI_KEY)

AREAS = ["Taman Melawati", "Wangsa Maju", "Setapak", "Ampang"]
QUERY_TYPES = ["aesthetic cafe", "family friendly cafe", "bakery cafe", "garden cafe"]

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": False
    }
    resp = requests.post(url, json=payload)
    resp.raise_for_status()

def fetch_real_places():
    selected_area = random.choice(AREAS)
    query_type = random.choice(QUERY_TYPES)
    search_query = f"{query_type} in {selected_area}, Kuala Lumpur"
    
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": PLACES_KEY.strip() if PLACES_KEY else "",
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.googleMapsUri,places.businessStatus,places.userRatingCount"
    }
    payload = {
        "textQuery": search_query,
        "minRating": 4.0
    }
    
    resp = requests.post(url, headers=headers, json=payload)
    print(f"Places API Response Code: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"Places API Error Body: {resp.text}")
        resp.raise_for_status()
        
    results = resp.json().get("places", [])
    
    operational_places = [
        p for p in results 
        if p.get("businessStatus") == "OPERATIONAL" and p.get("userRatingCount", 0) > 10
    ]
    
    if len(operational_places) >= 3:
        return random.sample(operational_places, 3)
    return operational_places

def evaluate_places_with_gemini(places):
    places_summary = ""
    for idx, p in enumerate(places, 1):
        name = p.get("displayName", {}).get("text", "Unknown")
        address = p.get("formattedAddress", "")
        maps_uri = p.get("googleMapsUri", "")
        places_summary += f"{idx}. Name: {name}\n   Address: {address}\n   Maps Link: {maps_uri}\n\n"

    prompt = f"""
    You are an expert family outing curator for Kuala Lumpur.
    
    Below are verified, currently operational cafes/spots retrieved directly from Google Places API:

    {places_summary}

    For EACH of the places listed above, evaluate them based on your knowledge of these real spots.
    
    Format output strictly as:

    ☕ **[Place Name]** ([Neighborhood/Area])
    📍 [Open in Google Maps]([Use exact Maps Link provided above])
    📸 [Search Instagram](https://www.instagram.com/explore/search/keyword/?q=[Place+Name+UrlEncoded])
    • **Aesthetics Rating:** ⭐ [X/5] - [Short design note]
    • **Kids Logistics Rating:** ⭐ [X/5] - [Short stroller/kids note]
    • **Summary:** [1-line summary]

    ---
    """

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )
    return response.text

if __name__ == "__main__":
    try:
        print("Fetching real venues from Google Places API (New)...")
        verified_places = fetch_real_places()
        
        if not verified_places:
            report = "No operational venues found in this search batch. Please re-roll again!"
        else:
            report = evaluate_places_with_gemini(verified_places)
            
        message = f"☕ **Verified Weekend Spot Recommendations** 🎈\n\n{report}"
        send_telegram_message(message)
        print("Successfully sent verified Places API recommendations to Telegram!")
    except Exception as e:
        print(f"Error during execution: {e}")
        raise e
        
