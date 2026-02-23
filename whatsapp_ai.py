import os
import psycopg2
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests

# Connect to PostgreSQL
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set in environment variables")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Create Flask app
app = Flask(__name__)

# Root route for testing
@app.route("/")
def home():
    return "Bot is running!"

# Twilio WhatsApp webhook
@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.values.get('Body', '')
    from_number = request.values.get('From', '')

    # Save user message to DB
    cur.execute(
        "INSERT INTO messages (user_number, role, content) VALUES (%s, %s, %s)",
        (from_number, 'user', incoming_msg)
    )
    conn.commit()

    # Fetch last 10 messages for context
    cur.execute(
        "SELECT role, content FROM messages WHERE user_number=%s ORDER BY created_at ASC LIMIT 10",
        (from_number,)
    )
    history = [{"role": row[0], "content": row[1]} for row in cur.fetchall()]

    # Call OpenRouter API
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
    if not OPENROUTER_API_KEY:
        return "OpenRouter API key not set", 500

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": history
    }

    try:
        response = requests.post(url, json=data, headers=headers, timeout=15)
        response.raise_for_status()
        reply_text = response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        reply_text = "Sorry, I couldn't process your message."

    # Save AI reply to DB
    cur.execute(
        "INSERT INTO messages (user_number, role, content) VALUES (%s, %s, %s)",
        (from_number, 'assistant', reply_text)
    )
    conn.commit()

    # Respond to user
    resp = MessagingResponse()
    resp.message(reply_text)
    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)
