print("Webhook hit!")
print("Data received:", data)


import os
import psycopg2
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests

# -----------------------------
# CONFIG
# -----------------------------
DATABASE_URL = os.environ.get("DATABASE_URL")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set in environment variables")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not set in environment variables")

DATABASE_URL = DATABASE_URL.strip()

# -----------------------------
# DATABASE SETUP
# -----------------------------
try:
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            user_id TEXT PRIMARY KEY,
            chat_history TEXT
        )
    """)
    print("Connected to database successfully!")
except Exception as e:
    raise RuntimeError(f"Could not connect to database: {e}")

# -----------------------------
# FLASK APP
# -----------------------------
app = Flask(__name__)

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def get_memory(user_id):
    cursor.execute("SELECT chat_history FROM memory WHERE user_id=%s", (user_id,))
    row = cursor.fetchone()
    return row[0] if row else ""

def update_memory(user_id, chat_history):
    cursor.execute("""
        INSERT INTO memory(user_id, chat_history)
        VALUES (%s, %s)
        ON CONFLICT (user_id) DO UPDATE
        SET chat_history = EXCLUDED.chat_history
    """, (user_id, chat_history))

def ask_openrouter(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4.1-mini",
        "input": prompt
    }
    try:
        response = requests.post("https://api.openrouter.ai/v1/completions", json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data["output"][0]["content"]
    except Exception as e:
        print("OpenRouter API error:", e)
        return "Sorry, I couldn't process that. Try again later."

# -----------------------------
# WHATSAPP WEBHOOK
# -----------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.form
    print("Incoming WhatsApp data:", data)

    user_id = data.get("From")
    user_message = data.get("Body")

    if not user_id or not user_message:
        print("Invalid incoming message!")
        return "OK", 200  # Twilio requires 200 response

    # Get previous chat history
    chat_history = get_memory(user_id)

    # Build prompt for AI
    prompt = f"Chat history:\n{chat_history}\nUser: {user_message}\nAI:"
    ai_response = ask_openrouter(prompt)

    # Update memory
    new_history = f"{chat_history}\nUser: {user_message}\nAI: {ai_response}"
    update_memory(user_id, new_history)

    # Respond to WhatsApp
    resp = MessagingResponse()
    resp.message(ai_response)
    return str(resp)

# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

