import os
import psycopg2
from flask import Flask, request, jsonify
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
    # Create memory table if it doesn't exist
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
    if row:
        return row[0]
    return ""

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
    response = requests.post("https://api.openrouter.ai/v1/completions", json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
    return data["output"][0]["content"]

# -----------------------------
# WHATSAPP WEBHOOK
# -----------------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    # Make sure you know how WhatsApp sends the message JSON
    user_id = data["from"]           # sender's number
    user_message = data["message"]   # the text message

    # Get previous chat history
    chat_history = get_memory(user_id)

    # Append new message
    prompt = f"Chat history:\n{chat_history}\nUser: {user_message}\nAI:"
    ai_response = ask_openrouter(prompt)

    # Update memory
    new_history = f"{chat_history}\nUser: {user_message}\nAI: {ai_response}"
    update_memory(user_id, new_history)

    # Respond to WhatsApp
    # Your WhatsApp API sending depends on the provider (Twilio, Meta, etc.)
    # Example: returning JSON for webhook handler
    return jsonify({"reply": ai_response})

# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
