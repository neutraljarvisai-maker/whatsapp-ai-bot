print("🚀 VERSION 4 - MEMORY CONNECTED")

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
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"
DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY")

# 🔥 MEMORY SERVER URL
MEMORY_SERVER_URL = "https://your-memory-server.up.railway.app"

pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# =============================
# 🔐 BULLETPROOF DB LAYER
# =============================
def run_query(query, params=(), fetch=False):
    for attempt in range(2):
        conn = None
        cursor = None

        try:
            conn = psycopg2.connect(DATABASE_URL, sslmode="require")
            cursor = conn.cursor()

            cursor.execute(query, params)

            result = cursor.fetchall() if fetch else None
            conn.commit()
            return result

        except psycopg2.InterfaceError as e:
            print("Retrying DB (cursor issue):", e)
            if attempt == 1:
                return [] if fetch else None
            continue

        except Exception as e:
            print("DB ERROR:", e)
            return [] if fetch else None

        finally:
            if cursor:
                try: cursor.close()
                except: pass
            if conn:
                try: conn.close()
                except: pass

    return [] if fetch else None

# =============================
# MEMORY SERVER 🔥
# =============================
def get_relevant_memory(uid, message):
    try:
        r = requests.post(
            f"{MEMORY_SERVER_URL}/retrieve",
            json={"user_id": uid, "message": message},
            timeout=3
        )
        return r.json()
    except Exception as e:
        print("Memory server failed:", e)
        return {
            "relevant_facts": "",
            "recent_chat": ""
        }

# =============================
# INIT TABLES
# =============================
tables = [
    """CREATE TABLE IF NOT EXISTS memory(user_id TEXT PRIMARY KEY, chat_history TEXT)""",
    """CREATE TABLE IF NOT EXISTS profile_memory(user_id TEXT PRIMARY KEY, facts TEXT)""",
    """CREATE TABLE IF NOT EXISTS interests(user_id TEXT, interest TEXT, level INTEGER DEFAULT 1,
       PRIMARY KEY(user_id,interest))""",
    """CREATE TABLE IF NOT EXISTS tasks(id SERIAL PRIMARY KEY, user_id TEXT, description TEXT,
       status TEXT DEFAULT 'pending', attempts INTEGER DEFAULT 0,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS goals(id SERIAL PRIMARY KEY, user_id TEXT, goal TEXT,
       progress INTEGER DEFAULT 0,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS last_seen(user_id TEXT PRIMARY KEY, last_time TIMESTAMP)"""
]

for t in tables:
    run_query(t)

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
# AI CALL
# =============================
def ask(message, facts="", context=""):
    try:
        r = groq.chat.completions.create(
            messages=[
                {"role":"system","content":PERSONALITY},
                {"role":"system","content":f"User Facts:\n{facts}"},
                {"role":"system","content":f"Relevant Context:\n{context}"},
                {"role":"user","content":message}
            ],
            model="llama-3.1-8b-instant"
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        print("Groq error:", e)
        return "⚠️ AI temporarily unavailable."

# =============================
# EXISTING MEMORY
# =============================
def get_profile(uid):
    r = run_query("SELECT facts FROM profile_memory WHERE user_id=%s", (uid,), True)
    return r[0][0] if r else ""

# =============================
# INTERESTS
# =============================
def learn_interest(uid, msg):
    topics = ["sports","tech","finance","study","cars","entertainment"]
    for t in topics:
        if t in msg.lower():
            run_query("""
                INSERT INTO interests(user_id, interest, level)
                VALUES(%s,%s,1)
                ON CONFLICT(user_id,interest)
                DO UPDATE SET level = interests.level + 1
            """, (uid, t))

# =============================
# LAST SEEN
# =============================
def update_last_seen(uid):
    run_query("""
        INSERT INTO last_seen(user_id, last_time)
        VALUES (%s,%s)
        ON CONFLICT(user_id)
        DO UPDATE SET last_time=EXCLUDED.last_time
    """, (uid, datetime.now()))

# =============================
# TASKS + GOALS
# =============================
def detect_task(msg):
    t = ask(f"Task to do later? Return task or NONE.\n{msg}")
    return t if t.upper() != "NONE" else None

def add_task(uid, desc):
    run_query("INSERT INTO tasks(user_id, description) VALUES(%s,%s)", (uid, desc))

def detect_goal(msg):
    g = ask(f"Long-term goal? Return goal or NONE.\n{msg}")
    return g if g.upper() != "NONE" else None

def add_goal(uid, goal):
    run_query("INSERT INTO goals(user_id, goal) VALUES(%s,%s)", (uid, goal))

# =============================
# MEDIA
# =============================
def transcribe_audio(url):
    try:
        audio = requests.get(url).content
        headers = {
            "Authorization": f"Token {DEEPGRAM_API_KEY}",
            "Content-Type": "audio/ogg"
        }
        r = requests.post("https://api.deepgram.com/v1/listen",
                          headers=headers, data=audio)
        return r.json()["results"]["channels"][0]["alternatives"][0]["transcript"]
    except:
        return ""

# =============================
# WEBHOOK 🔥 UPDATED
# =============================
@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    try:
        f = request.form
        uid = f.get("From")
        msg = f.get("Body","")

        if not uid:
            return "OK"

        update_last_seen(uid)
        learn_interest(uid, msg)

        facts = get_profile(uid)

        # 🔥 NEW — GET SMART MEMORY
        memory = {}
        try:
            r = requests.post(
                f"{MEMORY_SERVER_URL}/retrieve",
                json={"user_id": uid, "message": msg},
                timeout=3
            )
            memory = r.json()
        except Exception as e:
            print("Memory server failed:", e)

        context = str(memory)

        # 🔥 UPDATED AI CALL
        reply = ask(msg, facts, context)

        r = MessagingResponse()
        r.message(reply)
        return str(r)

    except Exception as e:
        print("CRASH PREVENTED:", e)
        r = MessagingResponse()
        r.message("⚠️ Temporary issue. Try again.")
        return str(r)

# =============================
# RUN
# =============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
