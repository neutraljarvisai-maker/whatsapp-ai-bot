import os
import psycopg2
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from groq import Groq

# -----------------------------
# CONFIG
# -----------------------------
DATABASE_URL = os.environ.get("DATABASE_URL")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set in environment variables")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not set in environment variables")

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
# GROQ CLIENT (Jarvis brain 🧠)
# -----------------------------
client = Groq(api_key=GROQ_API_KEY)

# -----------------------------
# FLASK APP
# -----------------------------
app = Flask(__name__)

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def get_memory(user_id):
    try:
        cursor.execute(
            "SELECT chat_history FROM memory WHERE user_id=%s",
            (user_id,)
        )
        row = cursor.fetchone()
        return row[0] if row else ""
    except Exception as e:
        print(f"Database read error for user {user_id}: {e}")
        return ""


def update_memory(user_id, chat_history):
    try:
        cursor.execute("""
            INSERT INTO memory(user_id, chat_history)
            VALUES (%s, %s)
            ON CONFLICT (user_id) DO UPDATE
            SET chat_history = EXCLUDED.chat_history
        """, (user_id, chat_history))
    except Exception as e:
        print(f"Database update error for user {user_id}: {e}")


def ask_groq(prompt):
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are Jarvis, a smart, helpful AI assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.1-8b-instant"
        )

        return chat_completion.choices[0].message.content

    except Exception as e:
        print("Groq API error:", e)
        return "Sorry, I couldn't process that. Try again later."


# -----------------------------
# WHATSAPP WEBHOOK
# -----------------------------
@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    data = request.form
    print("Webhook hit! Data received:", data)

    user_id = data.get("From")
    user_message = data.get("Body")

    if not user_id or not user_message:
        print("Invalid incoming message!")
        return "OK", 200

    # Get previous chat history
    chat_history = get_memory(user_id)

    # Build prompt with memory
    prompt = f"Chat history:\n{chat_history}\nUser: {user_message}\nJarvis:"

    ai_response = ask_groq(prompt)

    # Update memory
    new_history = f"{chat_history}\nUser: {user_message}\nJarvis: {ai_response}"
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
