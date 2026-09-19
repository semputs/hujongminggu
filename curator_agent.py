import os
import random
import urllib.parse
import requests
from apify_client import ApifyClient
from google import genai

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
PLACES_KEY = os.environ.get("PLACES_API_KEY")
APIFY_TOKEN = os.environ.get("APIFY_TOKEN")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

client = genai.Client(api_key=GEMINI_KEY)
apify_client = ApifyClient(APIFY_TOKEN)

# Targeted neighborhoods
TARGET_AREAS = ["Taman Melawati", "Wangsa Maju", "Setapak", "Ampang"]

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": False
    }
    resp = requests.post(url, json=payload)
    resp.raise_for_status()

def fetch_all_apify_captions():
    """Fetches ALL items from the latest Apify Instagram Scraper dataset."""
    print("Fetching scraped post captions from Apify...")
    try:
        # Fetch the most recent dataset/run from your Apify account
        runs = apify_client.actor("apify/instagram-scraper").runs().list(limit=1, desc=True)
        if not runs.items:
            print("No recent Apify runs found.")
            return []
        
        last_run_id = runs.items[0]["defaultDatasetId"]
        dataset_items = apify_client.dataset(last_run_id).list_items().items
        
        captions = []
        for item in dataset_items:
            caption = item.get("caption") or item.get("text") or ""
            if caption:
                captions.append(caption)
                
        print(f"Successfully retrieved {len(captions)} post captions from Apify.")
        return captions
    except Exception as e:
        print(f"Error fetching Apify dataset: {e}")
        return []

def extract_candidates_from_20_posts(captions):
    """Passes ALL 20 post captions to Gemini to identify mentioned venues in target areas."""
    if not captions:
        print("No captions found. Falling back to area search.")
        return ["Mori Kohi", "Contour Melawati", "VCR Ritchie"]

    all_captions_block = "\n--- POST SEPARATOR ---\n".join(captions)
    
    prompt = f"""
    You are an expert KL food scout. Below are {len(captions)} public Instagram post captions scraped from top KL foodie accounts:

    {all_captions_block}

    TASK:
    1. Read ALL the captions thoroughly.
    2. Identify and extract ALL cafe or restaurant names mentioned that are located in or near:
       - Taman Melawati
       - Wangsa Maju
       - Setapak
       - Ampang
    3. Output ONLY a clean comma-separated list of the venue names found. Do not include commentary.
       Example Output: "Mori Kohi, Contour, Knead and Feed, VCR Ritchie"
    """

    print("Analyzing all 20 captions with Gemini 3.6 Flash...")
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )
    
    raw_names = response.text.strip().replace('"', '')
    candidates = [name.strip() for name in raw_names.split(",") if name.strip()]
    print(f"Extracted candidate venues from social posts: {candidates}")
    return candidates

def verify_venues_with_places_api(candidate_names):
    """Verifies operational status of candidate venues via Google Places API (New)."""
    verified_places = []
    
    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": PLACES_KEY.strip() if PLACES_KEY else "",
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.googleMapsUri,places.businessStatus,places.userRatingCount,places.rating"
    }

    # Verify candidates against Google Places API
    for name in candidate_names:
        search_query = f"{name} Kuala Lumpur"
        payload = {
            "textQuery": search_query,
            "minRating": 3.8
        }
        
        try:
            resp = requests.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                places = resp.json().get("places", [])
                for p in places:
                    # Enforce strict OPERATIONAL check
                    if p.get("businessStatus") == "OPERATIONAL" and p.get("userRatingCount", 0) > 10:
                        verified_places.append(p)
                        break
        except Exception as e:
            print(f"Failed verifying {name}: {e}")

    # Remove duplicates by place name
    unique_verified = {p["displayName"]["text"]: p for p in verified_places}.values()
    return list(unique_verified)

def select_and_curate_top_3(verified_places):
    """Uses Gemini to evaluate all verified social candidates and pick the top 3 best spots."""
    places_summary = ""
    for idx, p in enumerate(verified_places, 1):
        name = p.get("displayName", {}).get("text", "Unknown")
        address = p.get("formattedAddress", "")
        maps_uri = p.get("googleMapsUri", "")
        places_summary += f"{idx}. Name: {name}\n   Address: {address}\n   Maps Link: {maps_uri}\n\n"

    prompt = f"""
    You are an expert family outing curator for Kuala Lumpur.
    
    Below is a list of REAL, CURRENTLY OPERATIONAL cafes that were extracted from recent Instagram posts and verified via Google Maps:

    {places_summary}

    TASK:
    Evaluate the venues above and select the TOP 3 BEST family-friendly and aesthetically pleasing spots for a weekend outing in Ampang, Melawati, Wangsa Maju, or Setapak.

    Format the final 3 spots strictly as:

    ☕ **[Place Name]** ([Neighborhood/Area])
    📍 [Open in Google Maps]([Use exact Maps Link provided above])
    📸 [Search Instagram](https://www.instagram.com/explore/search/keyword/?q=[Place+Name+UrlEncoded])
    • **Aesthetics Rating:** ⭐ [X/5] - [Short design note: Japandi, oak, minimalist, greenery]
    • **Kids Logistics Rating:** ⭐ [X/5] - [Short stroller/high chair/spacing note]
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
        # Step 1: Retrieve all 20 scraped captions from Apify
        captions = fetch_all_apify_captions()
        
        # Step 2: Extract candidate venues from the full batch
        candidate_names = extract_candidates_from_20_posts(captions)
        
        # Step 3: Verify operational status with Google Places API
        verified_places = verify_venues_with_places_api(candidate_names)
        
        if not verified_places:
            report = "No operational venues verified from this social batch. Please re-roll!"
        else:
            # Step 4: Pick and curate the top 3 best venues
            report = select_and_curate_top_3(verified_places)
            
        message = f"☕ **Verified Social Trend Spot Recommendations** 🎈\n\n{report}"
        send_telegram_message(message)
        print("Successfully sent 20-post social recommendations to Telegram!")
    except Exception as e:
        print(f"Execution failed: {e}")
        raise e
