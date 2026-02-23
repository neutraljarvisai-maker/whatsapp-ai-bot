import os
import psycopg2
import requests
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

# -----------------------------
# Connect to PostgreSQL
# -----------------------------
conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
cur = conn.cursor()

# -----------------------------
# Create Flask app
# -----------------------------
app = Flask(__name__)

# -----------------------------
# Root route for browser testing
# -----------------------------
@app.route("/")
def home():
    return "Bot is running!"

# -----------------------------
# Twilio WhatsApp webhook with memory
# -----------------------------
@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    # Get incoming message from Twilio
    from_number = request.values.get('From')
    incoming_msg = request.values.get('Body', '')

    # -----------------------------
    # 1️⃣ Save user message to database
    # -----------------------------
    cur.execute(
        "INSERT INTO messages (user_number, role, message) VALUES (%s, %s, %s)",
        (from_number, 'user', incoming_msg)
    )
    conn.commit()

    # -----------------------------
    # 2️⃣ Load conversation history for this user
    # -----------------------------
    cur.execute(
        "SELECT role, message FROM messages WHERE user_number=%s ORDER BY timestamp ASC",
        (from_number,)
    )
    conversation_history = cur.fetchall()  # list of tuples (role, message)

    # Convert to OpenRouter format
    messages = [{"role": role, "content": message} for role, message in conversation_history]

    # -----------------------------
    # 3️⃣ Call OpenRouter API
    # -----------------------------
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
        "messages": messages
    }

    try:
        response = requests.post(url, json=data, headers=headers, timeout=15)
        response.raise_for_status()
        reply_text = response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print("OpenRouter error:", e)
        reply_text = "Sorry, I couldn't process your message."

    # -----------------------------
    # 4️⃣ Save bot reply to database
    # -----------------------------
    cur.execute(
        "INSERT INTO messages (user_number, role, message) VALUES (%s, %s, %s)",
        (from_number, 'bot', reply_text)
    )
    conn.commit()

    # -----------------------------
    # 5️⃣ Send reply to WhatsApp
    # -----------------------------
    resp = MessagingResponse()
    resp.message(reply_text)
    return str(resp)

# -----------------------------
# Entry point for gunicorn
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
