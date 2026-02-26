import os
import psycopg2
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from groq import Groq
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import requests
from PIL import Image
import pytesseract
# =============================
# 📅 GOOGLE CALENDAR SETUP
# =============================
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dateutil import parser

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")

# Temporary token storage (later we can save in DB)
TOKEN_FILE = "token.json"

def get_calendar_service():
    creds = Credentials.from_authorized_user_file(TOKEN_FILE)
    return build("calendar", "v3", credentials=creds)

def create_event(text):
    service = get_calendar_service()

    # Try to extract date/time from message
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
# DATABASE
# =============================
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

cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    user_id TEXT,
    description TEXT,
    status TEXT DEFAULT 'pending',
    attempts INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS goals (
    id SERIAL PRIMARY KEY,
    user_id TEXT,
    goal TEXT,
    progress INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS last_seen (
    user_id TEXT PRIMARY KEY,
    last_time TIMESTAMP
)
""")

# =============================
# CLIENTS
# =============================
groq = Groq(api_key=GROQ_API_KEY)
twilio = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
app = Flask(__name__)

PERSONALITY = """
You are Jarvis — calm, intelligent, loyal, proactive,
slightly witty, and protective of the user.
"""

# =============================
# UTILITIES
# =============================
def send_whatsapp(to, msg):
    twilio.messages.create(body=msg, from_=TWILIO_WHATSAPP_NUMBER, to=to)

def ask(prompt, facts=""):
    r = groq.chat.completions.create(
        messages=[
            {"role":"system","content":PERSONALITY + f"\nUser facts:\n{facts}"},
            {"role":"user","content":prompt}
        ],
        model="llama-3.1-8b-instant"
    )
    return r.choices[0].message.content.strip()

# =============================
# MEMORY
# =============================
def get_memory(uid):
    cursor.execute("SELECT chat_history FROM memory WHERE user_id=%s",(uid,))
    r = cursor.fetchone()
    return r[0] if r else ""

def update_memory(uid, text):
    cursor.execute("""
    INSERT INTO memory VALUES (%s,%s)
    ON CONFLICT(user_id) DO UPDATE SET chat_history=EXCLUDED.chat_history
    """,(uid,text))

def get_profile(uid):
    cursor.execute("SELECT facts FROM profile_memory WHERE user_id=%s",(uid,))
    r = cursor.fetchone()
    return r[0] if r else ""

# =============================
# LAST SEEN TRACKING
# =============================
def update_last_seen(uid):
    cursor.execute("""
    INSERT INTO last_seen VALUES (%s,%s)
    ON CONFLICT(user_id) DO UPDATE SET last_time=EXCLUDED.last_time
    """,(uid, datetime.now()))

def get_last_seen(uid):
    cursor.execute("SELECT last_time FROM last_seen WHERE user_id=%s",(uid,))
    r = cursor.fetchone()
    return r[0] if r else None

# =============================
# 🎙️ VOICE TRANSCRIPTION (DEEPGRAM)
# =============================
def transcribe_audio(url):

    audio = requests.get(url).content

    dg_url = "https://api.deepgram.com/v1/listen"

    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "audio/ogg"
    }

    r = requests.post(dg_url, headers=headers, data=audio)

    try:
        return r.json()["results"]["channels"][0]["alternatives"][0]["transcript"]
    except:
        return ""

# =============================
# TASK SYSTEM
# =============================
def detect_task(msg):
    t = ask(f"Is this something to do later? Return task or NONE.\n{msg}")
    return t if t.upper() != "NONE" else None

def add_task(uid, desc):
    cursor.execute(
        "INSERT INTO tasks(user_id,description) VALUES (%s,%s)",
        (uid, desc)
    )

def pending(uid):
    cursor.execute(
        "SELECT id, description, attempts, created_at FROM tasks WHERE user_id=%s AND status='pending'",
        (uid,)
    )
    return cursor.fetchall()

# =============================
# 🎯 GOALS
# =============================
def detect_goal(msg):
    g = ask(f"Is this a long-term life goal? Return goal or NONE.\n{msg}")
    return g if g.upper() != "NONE" else None

def add_goal(uid, goal):
    cursor.execute(
        "INSERT INTO goals(user_id,goal) VALUES (%s,%s)",
        (uid, goal)
    )

# =============================
# 🧠 INTELLIGENT CHECK ENGINE
# =============================
def intelligent_check():

    tasks = pending(YOUR_NUMBER)

    for tid, desc, attempts, created in tasks:
        age = (datetime.now() - created).total_seconds() / 60

        if age > 120 and attempts == 0:
            send_whatsapp(YOUR_NUMBER, f"⏳ Reminder: {desc}")
            cursor.execute("UPDATE tasks SET attempts=1 WHERE id=%s",(tid,))

        elif age > 360 and attempts == 1:
            send_whatsapp(YOUR_NUMBER, f"⚠️ You still haven't started: {desc}")
            cursor.execute("UPDATE tasks SET attempts=2 WHERE id=%s",(tid,))

        elif age > 720 and attempts >= 2:
            send_whatsapp(
                YOUR_NUMBER,
                f"🚨 This task is overdue: {desc}\nWant me to break it into steps?"
            )
            cursor.execute("UPDATE tasks SET attempts=3 WHERE id=%s",(tid,))

# =============================
# 📅 DAILY PLANNER
# =============================
def planner():
    tasks = pending(YOUR_NUMBER)

    if tasks:
        msg = "📅 Suggested plan for today:\n\n"
        for t in tasks[:5]:
            msg += f"• {t[1]}\n"
        send_whatsapp(YOUR_NUMBER, msg)

# =============================
# 💤 INACTIVITY CHECK
# =============================
def inactivity_check():

    last = get_last_seen(YOUR_NUMBER)
    if not last:
        return

    if datetime.now() - last > timedelta(hours=8):
        send_whatsapp(
            YOUR_NUMBER,
            "👀 You’ve been quiet for a while. Everything okay?"
        )

# =============================
# 🌅 DAILY AUTONOMOUS SYSTEM
# =============================
def daily_updates():

    now = datetime.now()

    if now.hour == 5 and now.minute == 0:
        planner()

    if now.hour == 21 and now.minute == 0:
        cursor.execute(
            "SELECT goal, progress FROM goals WHERE user_id=%s",
            (YOUR_NUMBER,)
        )
        goals = cursor.fetchall()

        if goals:
            msg = "🎯 Goals check-in:\n\n"
            for g in goals:
                msg += f"• {g[0]} ({g[1]}%)\n"
            send_whatsapp(YOUR_NUMBER, msg)

    intelligent_check()
    inactivity_check()

# =============================
# WHATSAPP WEBHOOK
# =============================
@app.route("/whatsapp",methods=["POST"])
def whatsapp():

    f = request.form
    uid = f.get("From")
    msg = f.get("Body","")
    media = f.get("MediaUrl0")
    mtype = f.get("MediaContentType0")

    if not uid:
        return "OK"

    update_last_seen(uid)

    # 🎙️ Voice note → Deepgram
    if media and mtype and "audio" in mtype:
        msg += "\n" + transcribe_audio(media)

    # 🖼️ Image OCR
    if media and mtype and mtype.startswith("image"):
        img = requests.get(media).content
        open("tmp.jpg","wb").write(img)
        msg += "\n" + pytesseract.image_to_string(Image.open("tmp.jpg"))

    hist = get_memory(uid)
    facts = get_profile(uid)

    task = detect_task(msg)
    if task:
        add_task(uid, task)

    goal = detect_goal(msg)
    if goal:
        add_goal(uid, goal)

    prompt = f"{hist}\nUser:{msg}\nJarvis:"
    reply = ask(prompt, facts)

    update_memory(uid, hist + f"\nUser:{msg}\nJarvis:{reply}")

    r = MessagingResponse()
    r.message(reply)
    return str(r)

# =============================
# TEST ROUTE
# =============================
@app.route("/test-send")
def test():
    send_whatsapp(YOUR_NUMBER, "Jarvis V2 online ⚡")
    return "OK"


# =============================
# 🔐 GOOGLE AUTH ROUTES
# =============================
from google_auth_oauthlib.flow import Flow

@app.route("/authorize")
def authorize():
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [
                    "https://whatsapp-ai-bot-production-bc04.up.railway.app/callback"
                ],
            }
        },
        scopes=["https://www.googleapis.com/auth/calendar"],
    )

    flow.redirect_uri = "https://whatsapp-ai-bot-production-bc04.up.railway.app/callback"

    auth_url, _ = flow.authorization_url(prompt="consent")

    return f'<a href="{auth_url}">Authorize Calendar Access</a>'


@app.route("/callback")
def callback():
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [
                    "https://whatsapp-ai-bot-production-bc04.up.railway.app/callback"
                ],
            }
        },
        scopes=["https://www.googleapis.com/auth/calendar"],
    )

    flow.redirect_uri = "https://whatsapp-ai-bot-production-bc04.up.railway.app/callback"

    flow.fetch_token(authorization_response=request.url)

    creds = flow.credentials

    with open("token.json", "w") as f:
        f.write(creds.to_json())

    return "✅ Calendar connected! You can close this tab."

# =============================
# SCHEDULER
# =============================
sched = BackgroundScheduler()
sched.add_job(daily_updates, "interval", minutes=1)
sched.start()

# =============================
# RUN
# =============================
if __name__=="__main__":
    port=int(os.environ.get("PORT",8080))
    app.run(host="0.0.0.0",port=port)

