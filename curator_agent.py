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

# Target neighborhoods to randomly cycle through
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
    print(f"Telegram API Status: {resp.status_code}")
    resp.raise_for_status()

def fetch_real_places():
    selected_area = random.choice(AREAS)
    query_type = random.choice(QUERY_TYPES)
    search_query = f"{query_type} in {selected_area}, Kuala Lumpur"
    
    # Standard Places API endpoint (100% compatible with all enabled Google Cloud keys)
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={urllib.parse.quote(search_query)}&key={PLACES_KEY}"
    
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    
    if data.get("status") != "OK":
        print(f"Places API Status Error: {data.get('status')} - {data.get('error_message')}")
        return []

    results = data.get("results", [])
    
    operational_places = []
    for p in results:
        if p.get("business_status") == "OPERATIONAL" and p.get("user_ratings_total", 0) > 20:
            place_id = p.get("place_id")
            operational_places.append({
                "displayName": {"text": p.get("name")},
                "formattedAddress": p.get("formatted_address"),
                "rating": p.get("rating"),
                "googleMapsUri": f"https://www.google.com/maps/place/?q=place_id:{place_id}"
            })
            
    if len(operational_places) >= 3:
        return random.sample(operational_places, 3)
    return operational_places

def evaluate_places_with_gemini(places):
    """Passes verified real places to Gemini 3.6 Flash for aesthetic & logistics evaluation."""
    places_summary = ""
    for idx, p in enumerate(places, 1):
        name = p.get("displayName", {}).get("text", "Unknown")
        address = p.get("formattedAddress", "")
        rating = p.get("rating", "N/A")
        maps_uri = p.get("googleMapsUri", "")
        places_summary += f"{idx}. Name: {name}\n   Address: {address}\n   Rating: {rating}\n   Maps Link: {maps_uri}\n\n"

    prompt = f"""
    You are an expert family outing curator for Kuala Lumpur.
    
    Below are verified, currently operational cafes/spots retrieved directly from Google Places API:

    {places_summary}

    For EACH of the places listed above, provide a kid/aesthetic evaluation based on your knowledge of these real venues.
    
    Format output strictly as:

    ☕ **[Place Name]** ([Neighborhood/Area])
    📍 [Open in Google Maps]([Use exact Maps Link provided above])
    📸 [Search Instagram](https://www.instagram.com/explore/search/keyword/?q=[Place+Name+UrlEncoded])
    • **Aesthetics Rating:** ⭐ [X/5] - [Short design note: Japandi, oak, minimalist, greenery]
    • **Kids Logistics Rating:** ⭐ [X/5] - [Short stroller/high chair/spacing note]
    • **Summary:** [1-line summary]

    ---
    """

    print("Generating evaluation with Gemini 3.6 Flash...")
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )
    return response.text

if __name__ == "__main__":
    try:
        print("Fetching real venues from Google Places API...")
        verified_places = fetch_real_places()
        
        if not verified_places:
            report = "No operational venues found in this re-roll batch. Please re-roll again!"
        else:
            report = evaluate_places_with_gemini(verified_places)
            
        message = f"☕ **Verified Weekend Spot Recommendations** 🎈\n\n{report}"
        send_telegram_message(message)
        print("Successfully sent verified Places API recommendations to Telegram!")
    except Exception as e:
        print(f"Error during execution: {e}")
        raise e
        
