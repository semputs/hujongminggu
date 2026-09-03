import os
import requests
from google import genai

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

client = genai.Client(api_key=GEMINI_KEY)

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    # Removed parse_mode to prevent Markdown formatting failures
    payload = {"chat_id": CHAT_ID, "text": text} 
    
    resp = requests.post(url, json=payload)
    
    # Print Telegram's exact response to the log
    print(f"Telegram API Status: {resp.status_code}")
    print(f"Telegram API Response: {resp.text}")
    
    # Force GitHub Actions to fail if Telegram returns an error
    resp.raise_for_status()

def evaluate_sample_spot():
    sample_post = """
    Aesthetic new cafe in KL! Features warm oak wood tables, neutral Japandi decor, 
    spacious ground-floor seating with no entry steps, and a dedicated kids play corner.
    """
    
    prompt = f"""
    You are an expert family outing curator evaluating a potential weekend spot in KL.
    
    Review this venue description/caption:
    "{sample_post}"
    
    Criteria:
    1. Aesthetic: Is it Japandi, warm, or minimalist?
    2. Family/Kid Friendliness: Stroller access, play areas, high chairs?
    3. Comfort: Not overly cramped.
    
    If it matches, summarize why in 3 brief bullet points.
    """
    
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt
    )
    
    return response.text

if __name__ == "__main__":
    print("Running Curator Agent...")
    report = evaluate_sample_spot()
    
    message = f"☕ Weekend Spot Recommendation 🎈\n\n{report}"
    send_telegram_message(message)
    print("Report process completed!")
    
