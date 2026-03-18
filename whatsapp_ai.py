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
from google_auth_oauthlib.flow import Flow

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
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
YOUR_NUMBER = os.environ.get("YOUR_NUMBER")
DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY")

pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# =============================
# 🔐 SAFE DATABASE LAYER (FIXED)
# =============================
def get_connection():
    return psycopg2.connect(
        DATABASE_URL,
        sslmode="require",
        connect_timeout=10,
        keepalives=1,
        keepalives_idle=30,
        keepalives_interval=10,
        keepalives_count=5,
    )

def run_query(query, params=(), fetch=False):
    def execute_once():
        conn = None
        cursor = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)

            result = cursor.fetchall() if fetch else None
            conn.commit()
            return result

        finally:
            if cursor:
                try: cursor.close()
                except: pass
            if conn:
                try: conn.close()
                except: pass

    try:
        return execute_once()

    except psycopg2.InterfaceError as e:
        print("Retrying DB due to closed cursor:", e)
        try:
            return execute_once()
        except Exception as e2:
            print("DB ERROR (retry failed):", e2)
            return [] if fetch else None

    except Exception as e:
        print("DB ERROR:", e)
        return [] if fetch else None

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
# UTILITIES
# =============================
def send_whatsapp(to, msg):
    twilio.messages.create(body=msg, from_=TWILIO_WHATSAPP_NUMBER, to=to)

def ask(prompt, facts=""):
    try:
        r = groq.chat.completions.create(
            messages=[
                {"role":"system","content":PERSONALITY + "\nFacts:\n" + facts},
                {"role":"user","content":prompt}
            ],
            model="llama-3.1-8b-instant"
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        print("Groq error:", e)
        return "System overload. Try again."

# =============================
# MEMORY
# =============================
def get_memory(uid):
    r = run_query("SELECT chat_history FROM memory WHERE user_id=%s", (uid,), True)
    return r[0][0] if r else ""

def update_memory(uid, text):
    run_query("""
        INSERT INTO memory(user_id, chat_history) VALUES (%s,%s)
        ON CONFLICT(user_id) DO UPDATE SET chat_history=EXCLUDED.chat_history
    """, (uid, text))

def get_profile(uid):
    r = run_query("SELECT facts FROM profile_memory WHERE user_id=%s", (uid,), True)
    return r[0][0] if r else ""

# =============================
# INTEREST LEARNING
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
# TASK + GOALS
# =============================
def detect_task(msg):
    t = ask(f"Task to do later? Return task or NONE.\n{msg}")
    return t if t.upper() != "NONE" else None

def add_task(uid, desc):
    run_query("INSERT INTO tasks(user_id, description) VALUES(%s,%s)", (uid, desc))

def pending(uid):
    return run_query(
        "SELECT * FROM tasks WHERE user_id=%s AND status='pending'",
        (uid,), True)

def detect_goal(msg):
    g = ask(f"Long-term goal? Return goal or NONE.\n{msg}")
    return g if g.upper() != "NONE" else None

def add_goal(uid, goal):
    run_query("INSERT INTO goals(user_id, goal) VALUES(%s,%s)", (uid, goal))

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

def get_last_seen(uid):
    r = run_query(
        "SELECT last_time FROM last_seen WHERE user_id=%s",
        (uid,), True)
    return r[0][0] if r else None

# =============================
# VOICE → DEEPGRAM
# =============================
def transcribe_audio(url):
    audio = requests.get(url).content
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "audio/ogg"
    }
    r = requests.post("https://api.deepgram.com/v1/listen",
                      headers=headers, data=audio)
    try:
        return r.json()["results"]["channels"][0]["alternatives"][0]["transcript"]
    except:
        return ""

# =============================
# WHATSAPP WEBHOOK
# =============================
@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    f = request.form
    uid = f.get("From")
    msg = f.get("Body","")
    media = f.get("MediaUrl0")
    mtype = f.get("MediaContentType0")

    if not uid:
        return "OK"

    update_last_seen(uid)

    # Calendar
    if any(x in msg.lower() for x in ["schedule","add","remind"]):
        try:
            create_event(msg)
            r = MessagingResponse()
            r.message("📅 Event added.")
            return str(r)
        except:
            pass

    # Voice
    if media and mtype and "audio" in mtype:
        msg += "\n" + transcribe_audio(media)

    # Image OCR
    if media and mtype and mtype.startswith("image"):
        img = requests.get(media).content
        open("tmp.jpg","wb").write(img)
        msg += "\n" + pytesseract.image_to_string(Image.open("tmp.jpg"))

    learn_interest(uid, msg)

    hist = get_memory(uid)
    facts = get_profile(uid)

    task = detect_task(msg)
    if task:
        add_task(uid, task)

    goal = detect_goal(msg)
    if goal:
        add_goal(uid, goal)

    reply = ask(hist+"\nUser:"+msg+"\nJarvis:", facts)
    update_memory(uid, hist+f"\nUser:{msg}\nJarvis:{reply}")

    r = MessagingResponse()
    r.message(reply)
    return str(r)

# =============================
# RUN
# =============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT",8080))
    app.run(host="0.0.0.0", port=port)
