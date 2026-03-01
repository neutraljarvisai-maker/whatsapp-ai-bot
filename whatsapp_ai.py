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
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import Flow

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
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
TOKEN_FILE = "token.json"

pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

# =============================
# FLASK + CLIENTS
# =============================
app = Flask(__name__)
groq = Groq(api_key=GROQ_API_KEY)
twilio = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

PERSONALITY = """
You are Jarvis — calm, intelligent, loyal, proactive,
slightly witty, protective, and helpful.
"""

# =============================
# DATABASE UTILITY
# =============================
def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS memory(
        user_id TEXT PRIMARY KEY, chat_history TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS profile_memory(
        user_id TEXT PRIMARY KEY, facts TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS interests(
        user_id TEXT, interest TEXT, level INTEGER DEFAULT 1,
        PRIMARY KEY(user_id,interest))""")
    cur.execute("""CREATE TABLE IF NOT EXISTS tasks(
        id SERIAL PRIMARY KEY, user_id TEXT, description TEXT,
        status TEXT DEFAULT 'pending', attempts INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS goals(
        id SERIAL PRIMARY KEY, user_id TEXT, goal TEXT,
        progress INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS last_seen(
        user_id TEXT PRIMARY KEY, last_time TIMESTAMP)""")
    conn.commit()
    cur.close()
    conn.close()

init_db()

# =============================
# GOOGLE CALENDAR
# =============================
def get_calendar_service():
    creds = Credentials.from_authorized_user_file(TOKEN_FILE)
    return build("calendar", "v3", credentials=creds)

def create_event(text):
    service = get_calendar_service()
    dt = parser.parse(text, fuzzy=True)
    event = {
        "summary": text,
        "start": {"dateTime": dt.isoformat(), "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": (dt + timedelta(hours=1)).isoformat(), "timeZone": "Asia/Kolkata"},
    }
    service.events().insert(calendarId="primary", body=event).execute()

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
        return "I'm a bit overloaded right now. Try again in a moment."

# =============================
# DATABASE OPERATIONS
# =============================
def get_memory(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT chat_history FROM memory WHERE user_id=%s", (uid,))
    r = cur.fetchone()
    cur.close()
    conn.close()
    return r[0] if r else ""

def update_memory(uid, text):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO memory(user_id, chat_history) VALUES (%s,%s)
        ON CONFLICT(user_id) DO UPDATE SET chat_history=EXCLUDED.chat_history
    """, (uid, text))
    conn.commit()
    cur.close()
    conn.close()

def get_profile(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT facts FROM profile_memory WHERE user_id=%s", (uid,))
    r = cur.fetchone()
    cur.close()
    conn.close()
    return r[0] if r else ""

def learn_interest(uid, msg):
    topics = ["sports","tech","finance","study","cars","entertainment"]
    conn = get_conn()
    cur = conn.cursor()
    for t in topics:
        if t in msg.lower():
            cur.execute("""
                INSERT INTO interests(user_id, interest, level) VALUES(%s,%s,1)
                ON CONFLICT(user_id,interest)
                DO UPDATE SET level = interests.level + 1
            """, (uid, t))
    conn.commit()
    cur.close()
    conn.close()

def update_last_seen(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO last_seen(user_id, last_time)
        VALUES (%s,%s)
        ON CONFLICT(user_id) DO UPDATE SET last_time=EXCLUDED.last_time
    """, (uid, datetime.now()))
    conn.commit()
    cur.close()
    conn.close()

def get_last_seen(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT last_time FROM last_seen WHERE user_id=%s", (uid,))
    r = cur.fetchone()
    cur.close()
    conn.close()
    return r[0] if r else None

def add_task(uid, desc):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks(user_id, description) VALUES (%s,%s)", (uid, desc))
    conn.commit()
    cur.close()
    conn.close()

def pending(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE user_id=%s AND status='pending'", (uid,))
    r = cur.fetchall()
    cur.close()
    conn.close()
    return r

def add_goal(uid, goal):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO goals(user_id, goal) VALUES (%s,%s)", (uid, goal))
    conn.commit()
    cur.close()
    conn.close()

# =============================
# AUDIO / IMAGE
# =============================
def transcribe_audio(url):
    audio = requests.get(url).content
    headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}", "Content-Type": "audio/ogg"}
    r = requests.post("https://api.deepgram.com/v1/listen", headers=headers, data=audio)
    try:
        return r.json()["results"]["channels"][0]["alternatives"][0]["transcript"]
    except:
        return ""

# =============================
# TASK / GOALS DETECTION
# =============================
def detect_task(msg):
    t = ask(f"Task to do later? Return task or NONE.\n{msg}")
    return t if t.upper()!="NONE" else None

def detect_goal(msg):
    g = ask(f"Long-term goal? Return goal or NONE.\n{msg}")
    return g if g.upper()!="NONE" else None

# =============================
# NAGGING + PLANNER
# =============================
def intelligent_check():
    tasks = pending(YOUR_NUMBER)
    for t in tasks:
        tid, uid, desc, status, attempts, created = t
        if created is None:
            continue
        age = (datetime.now()-created).total_seconds()/60
        if age>120 and attempts==0:
            send_whatsapp(YOUR_NUMBER, f"⏳ Reminder: {desc}")
            conn = get_conn(); cur = conn.cursor()
            cur.execute("UPDATE tasks SET attempts=1 WHERE id=%s", (tid,))
            conn.commit(); cur.close(); conn.close()
        elif age>360 and attempts==1:
            send_whatsapp(YOUR_NUMBER, f"⚠️ Still not started: {desc}")
            conn = get_conn(); cur = conn.cursor()
            cur.execute("UPDATE tasks SET attempts=2 WHERE id=%s", (tid,))
            conn.commit(); cur.close(); conn.close()
        elif age>720 and attempts>=2:
            send_whatsapp(YOUR_NUMBER, f"🚨 OVERDUE: {desc}")
            conn = get_conn(); cur = conn.cursor()
            cur.execute("UPDATE tasks SET attempts=3 WHERE id=%s", (tid,))
            conn.commit(); cur.close(); conn.close()

def planner():
    tasks = pending(YOUR_NUMBER)
    if tasks:
        msg = "📅 Plan for today:\n\n"
        for t in tasks[:5]:
            msg += f"• {t[2]}\n"
        send_whatsapp(YOUR_NUMBER, msg)

def inactivity_check():
    last = get_last_seen(YOUR_NUMBER)
    if last and datetime.now()-last > timedelta(hours=8):
        send_whatsapp(YOUR_NUMBER,"👀 You’ve been quiet. Everything okay?")

def daily_updates():
    intelligent_check()
    inactivity_check()

# =============================
# WHATSAPP WEBHOOK
# =============================
@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    f = request.form
    uid = f.get("From")
    msg = f.get("Body", "")
    media = f.get("MediaUrl0")
    mtype = f.get("MediaContentType0")

    if not uid:
        return "OK"

    update_last_seen(uid)

    if any(x in msg.lower() for x in ["schedule","add","remind"]):
        try:
            create_event(msg)
            r = MessagingResponse()
            r.message("📅 Event added to calendar.")
            return str(r)
        except:
            pass

    if media and mtype and "audio" in mtype:
        msg += "\n" + transcribe_audio(media)

    if media and mtype and mtype.startswith("image"):
        img = requests.get(media).content
        open("tmp.jpg", "wb").write(img)
        msg += "\n" + pytesseract.image_to_string(Image.open("tmp.jpg"))

    learn_interest(uid, msg)

    hist = get_memory(uid)
    facts = get_profile(uid)

    task = detect_task(msg)
    if task: add_task(uid, task)

    goal = detect_goal(msg)
    if goal: add_goal(uid, goal)

    reply = ask(hist + "\nUser:" + msg + "\nJarvis:", facts)

    update_memory(uid, hist + f"\nUser:{msg}\nJarvis:{reply}")

    r = MessagingResponse()
    r.message(reply)
    return str(r)

# =============================
# GOOGLE AUTH
# =============================
@app.route("/authorize")
def authorize():
    flow = Flow.from_client_config(
        {"web":{
            "client_id":GOOGLE_CLIENT_ID,
            "client_secret":GOOGLE_CLIENT_SECRET,
            "auth_uri":"https://accounts.google.com/o/oauth2/auth",
            "token_uri":"https://oauth2.googleapis.com/token",
            "redirect_uris":[
                "https://whatsapp-ai-bot-production-bc04.up.railway.app/callback"
            ]}},
        scopes=["https://www.googleapis.com/auth/calendar"])
    flow.redirect_uri="https://whatsapp-ai-bot-production-bc04.up.railway.app/callback"
    auth_url, _ = flow.authorization_url(prompt="consent")
    return f'<a href="{auth_url}">Authorize Calendar</a>'

@app.route("/callback")
def callback():
    flow = Flow.from_client_config(
        {"web":{
            "client_id":GOOGLE_CLIENT_ID,
            "client_secret":GOOGLE_CLIENT_SECRET,
            "auth_uri":"https://accounts.google.com/o/oauth2/auth",
            "token_uri":"https://oauth2.googleapis.com/token",
            "redirect_uris":[
                "https://whatsapp-ai-bot-production-bc04.up.railway.app/callback"
            ]}},
        scopes=["https://www.googleapis.com/auth/calendar"])
    flow.redirect_uri="https://whatsapp-ai-bot-production-bc04.up.railway.app/callback"
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials
    with open("token.json", "w") as f:
        f.write(creds.to_json())
    return "✅ Calendar connected!"

# =============================
# TEST ROUTE
# =============================
@app.route("/test-send")
def test():
    send_whatsapp(YOUR_NUMBER,"Jarvis FULL CORE online ⚡")
    return "OK"

# =============================
# RUN
# =============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
