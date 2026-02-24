import os
import psycopg2
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from groq import Groq
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

# -----------------------------
# CONFIG
# -----------------------------
DATABASE_URL = os.environ.get("DATABASE_URL")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")

TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"  # Twilio sandbox

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not set")

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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profile_memory (
            user_id TEXT PRIMARY KEY,
            facts TEXT
        )
    """)

    print("Connected to database successfully!")

except Exception as e:
    raise RuntimeError(f"Database error: {e}")

# -----------------------------
# CLIENTS
# -----------------------------
groq_client = Groq(api_key=GROQ_API_KEY)
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# -----------------------------
# FLASK APP
# -----------------------------
app = Flask(__name__)

# -----------------------------
# 📩 SEND WHATSAPP MESSAGE
# -----------------------------
def send_whatsapp_message(to_number, message):
    try:
        twilio_client.messages.create(
            body=message,
            from_=TWILIO_WHATSAPP_NUMBER,
            to=to_number
        )
        print("Message sent successfully!")
    except Exception as e:
        print("Twilio send error:", e)

# -----------------------------
# ⏰ JARVIS DAILY TASKS
# -----------------------------
def jarvis_daily_updates():

    now = datetime.now()
    hour = now.hour
    minute = now.minute

    # 🌅 5 AM briefing
    if hour == 5 and minute == 0:
        send_whatsapp_message(
            "whatsapp:+917204595135",  # 🔴 YOUR NUMBER
            "🌅 Good morning. Here is your daily briefing."
        )

    # 🌙 10 PM updates
    if hour == 22 and minute == 0:
        send_whatsapp_message(
            "whatsapp:+917204595135",  # 🔴 YOUR NUMBER
            "🌙 Here are your nightly updates."
        )

# -----------------------------
# MEMORY FUNCTIONS
# -----------------------------
def get_memory(user_id):
    cursor.execute(
        "SELECT chat_history FROM memory WHERE user_id=%s",
        (user_id,)
    )
    row = cursor.fetchone()
    return row[0] if row else ""


def update_memory(user_id, chat_history):
    cursor.execute("""
        INSERT INTO memory(user_id, chat_history)
        VALUES (%s, %s)
        ON CONFLICT (user_id) DO UPDATE
        SET chat_history = EXCLUDED.chat_history
    """, (user_id, chat_history))

# -----------------------------
# PROFILE MEMORY
# -----------------------------
def get_profile(user_id):
    cursor.execute(
        "SELECT facts FROM profile_memory WHERE user_id=%s",
        (user_id,)
    )
    row = cursor.fetchone()
    return row[0] if row else ""


def update_profile(user_id, facts):
    cursor.execute("""
        INSERT INTO profile_memory(user_id, facts)
        VALUES (%s, %s)
        ON CONFLICT (user_id) DO UPDATE
        SET facts = EXCLUDED.facts
    """, (user_id, facts))

# -----------------------------
# 🧠 FACT EXTRACTION
# -----------------------------
def extract_facts(old_facts, new_message):

    prompt = f"""
Existing facts:
{old_facts}

User message:
{new_message}

Extract important personal facts (interests, goals, preferences).
Return short bullet points.
If nothing new, return existing facts.
"""

    response = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": "Extract user facts."},
            {"role": "user", "content": prompt}
        ],
        model="llama-3.1-8b-instant"
    )

    return response.choices[0].message.content

# -----------------------------
# 🤖 ASK GROQ
# -----------------------------
def ask_groq(prompt, profile_facts):

    chat_completion = groq_client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"""
You are Jarvis, a calm, intelligent AI assistant.

Known facts about the user:
{profile_facts}

Use them naturally.
Speak professionally and helpfully.
"""
            },
            {"role": "user", "content": prompt}
        ],
        model="llama-3.1-8b-instant"
    )

    return chat_completion.choices[0].message.content

# -----------------------------
# 📱 WHATSAPP WEBHOOK
# -----------------------------
@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():

    data = request.form
    print("Webhook hit:", data)

    user_id = data.get("From")
    user_message = data.get("Body")

    if not user_id or not user_message:
        return "OK", 200

    chat_history = get_memory(user_id)
    profile_facts = get_profile(user_id)

    updated_facts = extract_facts(profile_facts, user_message)
    update_profile(user_id, updated_facts)

    prompt = f"Chat history:\n{chat_history}\nUser: {user_message}\nJarvis:"

    ai_response = ask_groq(prompt, updated_facts)

    new_history = f"{chat_history}\nUser: {user_message}\nJarvis: {ai_response}"
    update_memory(user_id, new_history)

    resp = MessagingResponse()
    resp.message(ai_response)

    return str(resp)

# -----------------------------
# 🧪 TEST ROUTE
# -----------------------------
@app.route("/test-send")
def test_send():

    send_whatsapp_message(
        "whatsapp:+917204595135",  # 🔴 YOUR NUMBER
        "Jarvis online ✅"
    )

    return "Sent!"

# -----------------------------
# 🚀 START SCHEDULER
# -----------------------------
scheduler = BackgroundScheduler()
scheduler.add_job(jarvis_daily_updates, "interval", minutes=1)
scheduler.start()

# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
