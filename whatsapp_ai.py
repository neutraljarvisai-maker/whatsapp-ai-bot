import os
import psycopg2

# Connect to PostgreSQL
conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
cur = conn.cursor()

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import os
import requests

# Create Flask app
app = Flask(__name__)

# Root route for testing in browser
@app.route("/")
def home():
    return "Bot is running!"

# Twilio WhatsApp webhook
@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    # Get the incoming message from Twilio
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
        "model": "gpt-4o-mini",  # You can change the model if you want
        "messages": [{"role": "user", "content": incoming_msg}]
    }

    try:
        response = requests.post(url, json=data, headers=headers, timeout=15)
        response.raise_for_status()
        reply_text = response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        reply_text = "Sorry, I couldn't process your message."

    # Create Twilio response
    resp = MessagingResponse()
    resp.message(reply_text)
    return str(resp)

# Entry point for gunicorn
if __name__ == "__main__":
    app.run(debug=True)

