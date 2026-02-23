import os
import psycopg2
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests

# =========================
# Database Connection Setup
# =========================
try:
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL not set in environment variables")

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    print("✅ Database connected successfully!")
except Exception as e:
    print("⚠️ Database connection failed:", e)
    conn = None
    cur = None

# =========================
# Flask App Setup
# =========================
app = Flask(__name__)

# Root route for testing in browser
@app.route("/")
def home():
    return "Bot is running!"

# Twilio WhatsApp webhook
@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.values.get('Body', '')

    # OpenRouter API key from environment
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
    if not OPENROUTER_API_KEY:
        return "OpenRouter API key not set", 500

    # Call OpenRouter API
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4o-mini",  # Change model if desired
        "messages": [{"role": "user", "content": incoming_msg}]
    }

    try:
        response = requests.post(url, json=data, headers=headers, timeout=15)
        response.raise_for_status()
        reply_text = response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print("⚠️ OpenRouter API failed:", e)
        reply_text = "Sorry, I couldn't process your message."

    # Optionally save message to database if connected
    if cur:
        try:
            cur.execute(
                "INSERT INTO messages (content) VALUES (%s);",
                (incoming_msg,)
            )
            conn.commit()
        except Exception as e:
            print("⚠️ Failed to save message to DB:", e)

    # Respond to WhatsApp
    resp = MessagingResponse()
    resp.message(reply_text)
    return str(resp)

# Entry point for Gunicorn
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
