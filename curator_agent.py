import os
import requests
import instaloader
from itertools import islice
from google import genai

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

client = genai.Client(api_key=GEMINI_KEY)

# Target Instagram accounts covering Wangsa Maju, Melawati & KL
TARGET_ACCOUNTS = [
    "kl.foodie",
    "klfoodhunter",
    "mycafefood",
    "myfunmy",
    "placesmalaysia"
]

# Preferred local areas to filter for
LOCAL_KEYWORDS = ["melawati", "wangsa maju", "setapak", "ampang", "kl", "kuala lumpur"]

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    resp = requests.post(url, json=payload)
    print(f"Telegram Status: {resp.status_code}")
    resp.raise_for_status()

def fetch_recent_posts():
    L = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        save_metadata=False
    )
    
    collected_posts = []
    
    for account in TARGET_ACCOUNTS:
        print(f"Scanning @{account}...")
        try:
            profile = instaloader.Profile.from_username(L.context, account)
            # Inspect the 5 latest posts per account
            for post in islice(profile.get_posts(), 5):
                caption = post.caption or ""
                caption_lower = caption.lower()
                
                # Pre-filter: Check if caption mentions target locations
                if any(kw in caption_lower for kw in LOCAL_KEYWORDS):
                    collected_posts.append({
                        "account": account,
                        "url": f"https://www.instagram.com/p/{post.shortcode}/",
                        "caption": caption[:1000] # Limit length
                    })
        except Exception as e:
            print(f"Error fetching @{account}: {e}")
            
    return collected_posts

def evaluate_post_with_gemini(post):
    prompt = f"""
    You are an expert family outing curator evaluating a venue for a weekend trip in KL (Melawati/Wangsa Maju area).
    
    Account: @{post['account']}
    Caption: "{post['caption']}"
    
    Criteria:
    1. Aesthetic: Is it Japandi, warm, or minimalist?
    2. Family/Kid Friendliness: Stroller access, play areas, high chairs, open spaces?
    3. Comfort: Not overly cramped.
    
    Determine if this place is a strong match for a family outing.
    If YES: Summarize why in 3 bullet points, note the venue name/location, and rate enthusiasm (1-5 stars).
    If NO: Reply strictly with "REJECT".
    """
    
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt
    )
    
    return response.text

if __name__ == "__main__":
    print("Starting Live Curator Agent...")
    posts = fetch_recent_posts()
    print(f"Found {len(posts)} potential local posts to evaluate.")
    
    matches_found = 0
    for post in posts:
        evaluation = evaluate_post_with_gemini(post)
        if "REJECT" not in evaluation.upper():
            matches_found += 1
            message = (
                f"☕ **New Family Spot Found!** 🎈\n"
                f"Source: @{post['account']}\n"
                f"Link: {post['url']}\n\n"
                f"{evaluation}"
            )
            send_telegram_message(message)
            
    if matches_found == 0:
        print("No new matching spots found in this run.")
    
