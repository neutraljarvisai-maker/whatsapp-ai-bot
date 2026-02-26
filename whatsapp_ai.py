import os
import psycopg2
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from groq import Groq
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import json
import requests
from PIL import Image
import pytesseract

# =============================
# CONFIG
# =============================
DATABASE_URL = os.environ.get("DATABASE_URL")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"
YOUR_NUMBER = os.environ.get("YOUR_NUMBER")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.environ.get("GOOGLE_CSE_ID")

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
CREATE TABLE IF NOT EXISTS interests (
    user_id TEXT,
    interest TEXT,
    level INTEGER DEFAULT 1,
    PRIMARY KEY (user_id, interest)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    user_id TEXT,
    description TEXT,
    status TEXT DEFAULT 'pending',
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 4,
    alternatives JSON DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# =============================
# CLIENTS
# =============================
groq = Groq(api_key=GROQ_API_KEY)
twilio = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

app = Flask(__name__)

# =============================
# UTILITIES
# =============================
def send_whatsapp(to, msg):
    twilio.messages.create(body=msg, from_=TWILIO_WHATSAPP_NUMBER, to=to)

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

def update_profile(uid,facts):
    cursor.execute("""
    INSERT INTO profile_memory VALUES (%s,%s)
    ON CONFLICT(user_id) DO UPDATE SET facts=EXCLUDED.facts
    """,(uid,facts))

# =============================
# GROQ HELPERS
# =============================
def ask(prompt, facts=""):
    r = groq.chat.completions.create(
        messages=[
            {"role":"system","content":f"You are Jarvis. Keep replies short. User facts:\n{facts}"},
            {"role":"user","content":prompt}
        ],
        model="llama-3.1-8b-instant"
    )
    return r.choices[0].message.content.strip()

def extract_facts(old, msg):
    p=f"Old facts:\n{old}\nMessage:\n{msg}\nUpdate facts briefly."
    return ask(p)

# =============================
# INTEREST SYSTEM
# =============================
CATS=["Sports","Entertainment","Tech","Study","Finance","Cars"]

def learn_interests(uid,msg):
    p=f"Detect interests from message. Categories:{CATS}. Return JSON list with topic and level 1-4.\n{msg}"
    try:
        j=json.loads(ask(p))
        for it in j:
            t=it["topic"].capitalize()
            l=max(1,min(4,it["level"]))
            cursor.execute("SELECT level FROM interests WHERE user_id=%s AND interest=%s",(uid,t))
            ex=cursor.fetchone()
            if ex:
                cursor.execute("UPDATE interests SET level=%s WHERE user_id=%s AND interest=%s",(max(ex[0],l),uid,t))
            else:
                cursor.execute("INSERT INTO interests VALUES (%s,%s,%s)",(uid,t,l))
    except:
        pass

# =============================
# GOOGLE SEARCH
# =============================
def google_search(q):
    url="https://www.googleapis.com/customsearch/v1"
    params={"key":GOOGLE_API_KEY,"cx":GOOGLE_CSE_ID,"q":q,"num":3}
    r=requests.get(url,params=params).json()
    if "items" not in r: return "No results."
    return "\n\n".join([f"{i['title']}\n{i['link']}" for i in r["items"]])

# =============================
# TASK SYSTEM
# =============================
def detect_task(msg):
    t=ask(f"Is this a task? Return task or NONE.\n{msg}")
    return t if t.upper()!="NONE" else None

def add_task(uid,desc):
    cursor.execute("INSERT INTO tasks(user_id,description) VALUES (%s,%s)",(uid,desc))

def pending(uid):
    cursor.execute("SELECT * FROM tasks WHERE user_id=%s AND status='pending'",(uid,))
    return cursor.fetchall()

def solve_task(t):
    tid,uid,desc,_,att,maxa,alts,_ = t
    alts=json.loads(alts) if alts else []

    res=ask(f"Solve this autonomously: {desc}")
    if "cannot" in res.lower() or "unable" in res.lower():
        alt=ask(f"Suggest alternative ways to do: {desc}")
        alts.append(alt)
        cursor.execute("UPDATE tasks SET attempts=attempts+1,alternatives=%s WHERE id=%s",(json.dumps(alts),tid))

        if att+1>=maxa:
            cursor.execute("UPDATE tasks SET status='failed' WHERE id=%s",(tid,))
            send_whatsapp(uid,f"⚠️ Task failed: {desc}")
    else:
        cursor.execute("UPDATE tasks SET status='done' WHERE id=%s",(tid,))
        send_whatsapp(uid,f"✅ Done: {desc}")

def run_tasks():
    for t in pending(YOUR_NUMBER):
        solve_task(t)

# =============================
# ⭐ AUTONOMOUS DECISION ENGINE
# =============================
def intelligent_check():
    now = datetime.now()

    cursor.execute("""
        SELECT id, description, created_at, attempts
        FROM tasks
        WHERE user_id=%s AND status='pending'
    """, (YOUR_NUMBER,))
    tasks = cursor.fetchall()

    if not tasks:
        return

    for tid, desc, created, attempts in tasks:
        age_minutes = (now - created).total_seconds() / 60

        if age_minutes > 720 and attempts >= 1:
            send_whatsapp(
                YOUR_NUMBER,
                f"🚨 Overdue task: {desc}\nWant help breaking it down?"
            )
            cursor.execute(
                "UPDATE tasks SET attempts=attempts+1 WHERE id=%s",
                (tid,)
            )

        elif age_minutes > 360 and attempts == 0:
            send_whatsapp(
                YOUR_NUMBER,
                f"⚠️ You still haven't started: {desc}"
            )
            cursor.execute(
                "UPDATE tasks SET attempts=attempts+1 WHERE id=%s",
                (tid,)
            )

        elif age_minutes > 120 and attempts == 0:
            send_whatsapp(
                YOUR_NUMBER,
                f"⏳ Reminder: {desc}"
            )
            cursor.execute(
                "UPDATE tasks SET attempts=attempts+1 WHERE id=%s",
                (tid,)
            )

# =============================
# DAILY UPDATES
# =============================
def daily_updates():
    now=datetime.now()

    if now.hour==5 and now.minute==0:
        msg="🌅 Morning briefing\n\nTasks:\n"
        msg+="\n".join([t[2] for t in pending(YOUR_NUMBER)]) or "None"

        cursor.execute("SELECT interest,level FROM interests WHERE user_id=%s AND level>=2",(YOUR_NUMBER,))
        ints=cursor.fetchall()
        for i,l in ints:
            msg+=f"\n\n📰 {i} news:\n{google_search(i+' news')}"
        send_whatsapp(YOUR_NUMBER,msg)

    if now.hour==22 and now.minute==0:
        cursor.execute("SELECT count(*) FROM tasks WHERE user_id=%s AND status='done'",(YOUR_NUMBER,))
        done=cursor.fetchone()[0]
        send_whatsapp(YOUR_NUMBER,f"🌙 Night report\nCompleted tasks: {done}")

    run_tasks()
    intelligent_check()   # ⭐ NEW

# =============================
# WHATSAPP WEBHOOK
# =============================
@app.route("/whatsapp",methods=["POST"])
def whatsapp():
    f=request.form
    uid=f.get("From")
    msg=f.get("Body","")
    media=f.get("MediaUrl0")
    mtype=f.get("MediaContentType0")

    if not uid: return "OK"

    # IMAGE OCR
    if media and mtype and mtype.startswith("image"):
        img=requests.get(media).content
        open("tmp.jpg","wb").write(img)
        text=pytesseract.image_to_string(Image.open("tmp.jpg"))
        msg+="\n"+text

    # MEMORY
    hist=get_memory(uid)
    facts=get_profile(uid)

    newfacts=extract_facts(facts,msg)
    update_profile(uid,newfacts)

    learn_interests(uid,msg)

    task=detect_task(msg)
    if task: add_task(uid,task)

    # SEARCH TRIGGER
    if msg.lower().startswith(("search","find","look up","tell me about")):
        reply=google_search(msg)
    else:
        prompt=f"{hist}\nUser:{msg}\nJarvis:"
        reply=ask(prompt,newfacts)

    update_memory(uid, hist+f"\nUser:{msg}\nJarvis:{reply}")

    r=MessagingResponse()
    r.message(reply)
    return str(r)

# =============================
# TEST ROUTE
# =============================
@app.route("/test-send")
def test():
    send_whatsapp(YOUR_NUMBER,"Jarvis online ✅")
    return "OK"

# =============================
# SCHEDULER
# =============================
sched=BackgroundScheduler()
sched.add_job(daily_updates,"interval",minutes=1)
sched.start()

# =============================
# RUN
# =============================
if __name__=="__main__":
    port=int(os.environ.get("PORT",8080))
    app.run(host="0.0.0.0",port=port)
