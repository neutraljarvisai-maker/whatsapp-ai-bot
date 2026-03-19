print("🚀 VERSION 4 (QUERY AI + LOW TOKENS)")

import os
import psycopg2
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from groq import Groq
from datetime import datetime, timedelta
import requests
from PIL import Image
import pytesseract
from dateutil import parser

# =============================
# 📅 GOOGLE CALENDAR SETUP
# =============================
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_FILE = "token.json"

def get_calendar_service():
    creds = Credentials.from_authorized_user_file(TOKEN_FILE)
    return build("calendar", "v3", credentials=creds)

def create_event(text):
    service = get_calendar_service()
    dt = parser.parse(text, fuzzy=True)
    event = {
        "summary": text,
        "start": {"dateTime": dt.isoformat(), "timeZone": "Asia/Kolkata"},
        "end": {
            "dateTime": (dt + timedelta(hours=1)).isoformat(),
            "timeZone": "Asia/Kolkata",
        },
    }
    service.events().insert(calendarId="primary", body=event).execute()

# =============================
# CONFIG
# =============================
DATABASE_URL = os.environ.get("DATABASE_URL")
MEMORY_SERVER_URL = os.environ.get("MEMORY_SERVER_URL")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

SUPABASE_FUNCTION_URL = "https://creaavsrhfxwshknjghh.supabase.co/functions/v1/query_ai"
SUPABASE_ANON_KEY = "YOUR_SUPABASE_ANON_KEY"

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY")

pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# =============================
# DB
# =============================
def run_query(query, params=(), fetch=False):
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchall() if fetch else None
        conn.commit()
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        print("DB ERROR:", e)
        return [] if fetch else None

# =============================
# CLIENTS
# =============================
groq = Groq(api_key=GROQ_API_KEY)
twilio = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
app = Flask(__name__)

PERSONALITY = """
You are Jarvis — calm, intelligent, loyal, proactive,
slightly witty, protective, and helpful.
"""

# =============================
# 🔥 QUERY AI FUNCTION
# =============================
def get_query_hints(user_message):
    try:
        r = requests.post(
            SUPABASE_FUNCTION_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
            },
            json={"question": user_message}
        )
        data = r.json()
        return data.get("hints", [])
    except Exception as e:
        print("Query AI Error:", e)
        return []

# =============================
# 🧠 SMART ASK (LOW TOKEN)
# =============================
def ask(user_message, recent_context, hints, facts=""):
    try:
        context_text = "\n".join(hints)

        prompt = f"""
User message:
{user_message}

Recent conversation:
{recent_context}

Relevant context:
{context_text}

User profile:
{facts}

Respond naturally and intelligently.
"""

        r = groq.chat.completions.create(
            messages=[
                {"role": "system", "content": PERSONALITY},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant"
        )

        return r.choices[0].message.content.strip()

    except Exception as e:
        print("Groq error:", e)
        return "⚠️ AI error."

# =============================
# MEMORY (SHORT CONTEXT ONLY)
# =============================
def get_recent_memory(uid):
    r = run_query(
        "SELECT chat_history FROM memory WHERE user_id=%s",
        (uid,),
        True
    )
    if not r:
        return ""

    full = r[0][0]

    # ONLY LAST 5 LINES (VERY IMPORTANT)
    lines = full.split("\n")
    return "\n".join(lines[-5:])

def update_memory(uid, text):
    run_query("""
        INSERT INTO memory(user_id, chat_history)
        VALUES (%s,%s)
        ON CONFLICT(user_id)
        DO UPDATE SET chat_history = memory.chat_history || %s
    """, (uid, text, text))

def get_profile(uid):
    r = run_query("SELECT facts FROM profile_memory WHERE user_id=%s", (uid,), True)
    return r[0][0] if r else ""

# =============================
# WEBHOOK
# =============================
@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    try:
        f = request.form
        uid = f.get("From")
        msg = f.get("Body", "")

        if not uid:
            return "OK"

        # 🔥 STEP 1: Get smart hints
        hints = get_query_hints(msg)

        # 🔥 STEP 2: Get SHORT memory
        recent = get_recent_memory(uid)

        # 🔥 STEP 3: Get profile
        facts = get_profile(uid)

        # 🔥 STEP 4: Ask AI
        reply = ask(msg, recent, hints, facts)

        # 🔥 STEP 5: Save memory
        update_memory(uid, f"\nUser:{msg}\nJarvis:{reply}")

        r = MessagingResponse()
        r.message(reply)
        return str(r)

    except Exception as e:
        print("CRASH:", e)
        r = MessagingResponse()
        r.message("⚠️ Temporary issue.")
        return str(r)

# =============================
# RUN
# =============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
