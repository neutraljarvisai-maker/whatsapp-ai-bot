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
import time

# -----------------------------
# CONFIG
# -----------------------------
DATABASE_URL = os.environ.get("DATABASE_URL")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"
YOUR_NUMBER = os.environ.get("YOUR_NUMBER")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.environ.get("GOOGLE_CSE_ID")

if not all([DATABASE_URL, GROQ_API_KEY, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, YOUR_NUMBER, GOOGLE_API_KEY, GOOGLE_CSE_ID]):
    raise ValueError("Please set all required environment variables!")

DATABASE_URL = DATABASE_URL.strip()

# -----------------------------
# DATABASE SETUP
# -----------------------------
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
    max_attempts INTEGER DEFAULT 3,
    alternatives JSON DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

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
# UTILITY FUNCTIONS
# -----------------------------
def send_whatsapp_message(to_number, message):
    twilio_client.messages.create(
        body=message,
        from_=TWILIO_WHATSAPP_NUMBER,
        to=to_number
    )

def get_memory(user_id):
    cursor.execute("SELECT chat_history FROM memory WHERE user_id=%s",(user_id,))
    row = cursor.fetchone()
    return row[0] if row else ""

def update_memory(user_id,chat_history):
    cursor.execute("INSERT INTO memory(user_id,chat_history) VALUES (%s,%s) ON CONFLICT(user_id) DO UPDATE SET chat_history=EXCLUDED.chat_history",(user_id,chat_history))

def get_profile(user_id):
    cursor.execute("SELECT facts FROM profile_memory WHERE user_id=%s",(user_id,))
    row = cursor.fetchone()
    return row[0] if row else ""

def update_profile(user_id,facts):
    cursor.execute("INSERT INTO profile_memory(user_id,facts) VALUES (%s,%s) ON CONFLICT(user_id) DO UPDATE SET facts=EXCLUDED.facts",(user_id,facts))

# -----------------------------
# TASK MANAGEMENT
# -----------------------------
def add_task(user_id, description, max_attempts=3):
    cursor.execute("INSERT INTO tasks(user_id,description,max_attempts) VALUES (%s,%s,%s)",(user_id,description,max_attempts))

def get_pending_tasks(user_id):
    cursor.execute("SELECT id, description, status, attempts, max_attempts, alternatives FROM tasks WHERE user_id=%s AND status='pending' ORDER BY created_at",(user_id,))
    return cursor.fetchall()

def mark_task_done(task_id):
    cursor.execute("UPDATE tasks SET status='done' WHERE id=%s",(task_id,))

def increment_task_attempts(task_id):
    cursor.execute("UPDATE tasks SET attempts=attempts+1 WHERE id=%s RETURNING attempts",(task_id,))
    return cursor.fetchone()[0]

def update_task_alternatives(task_id, alternatives):
    cursor.execute("UPDATE tasks SET alternatives=%s WHERE id=%s",(json.dumps(alternatives),task_id))

# -----------------------------
# INTEREST TRACKING
# -----------------------------
INTEREST_CATEGORIES = ["Sports","Entertainment","Tech","Study","Finance","Cars"]

def extract_interests(message):
    prompt = f"""
Extract personal interests from this message. Use only these categories:
{', '.join(INTEREST_CATEGORIES)}
Return JSON: {{ "interests": [{{"topic":"...", "level":1-4}}] }}
Levels: 1=casual,2=moderate,3=strong,4=hardcore
Message:
{message}
"""
    response = groq_client.chat.completions.create(
        messages=[{"role":"system","content":"Extract interests."},{"role":"user","content":prompt}],
        model="llama-3.1-8b-instant"
    )
    try:
        return json.loads(response.choices[0].message.content)["interests"]
    except:
        return []

def update_interests(user_id, interests):
    for item in interests:
        topic = item["topic"].capitalize()
        level = max(1,min(4,item["level"]))
        cursor.execute("SELECT level FROM interests WHERE user_id=%s AND interest=%s",(user_id,topic))
        existing = cursor.fetchone()
        if existing:
            new_level = max(existing[0],level)
            cursor.execute("UPDATE interests SET level=%s WHERE user_id=%s AND interest=%s",(new_level,user_id,topic))
        else:
            cursor.execute("INSERT INTO interests(user_id,interest,level) VALUES (%s,%s,%s)",(user_id,topic,level))

# -----------------------------
# GOOGLE SEARCH
# -----------------------------
def google_search(query, num_results=3):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {"key":GOOGLE_API_KEY,"cx":GOOGLE_CSE_ID,"q":query,"num":num_results}
    try:
        response = requests.get(url,params=params)
        data = response.json()
        items = data.get("items",[])
        if not items: return "I couldn't find anything useful."
        results_text = ""
        for i,item in enumerate(items,1):
            title = item.get("title","No title")
            snippet = item.get("snippet","")
            link = item.get("link","")
            results_text += f"{i}. {title}\n{snippet}\n{link}\n\n"
        return results_text.strip()
    except Exception as e:
        return f"Error fetching search results: {e}"

# -----------------------------
# GROQ AI FUNCTIONS
# -----------------------------
def extract_facts(old_facts,new_message):
    prompt=f"Existing facts:\n{old_facts}\nUser message:\n{new_message}\nExtract important personal facts in short bullet points."
    response = groq_client.chat.completions.create(
        messages=[{"role":"system","content":"Extract user facts."},{"role":"user","content":prompt}],
        model="llama-3.1-8b-instant"
    )
    return response.choices[0].message.content.strip()

def ask_groq(prompt,profile_facts):
    response = groq_client.chat.completions.create(
        messages=[{"role":"system","content":f"You are Jarvis. Known facts about user:\n{profile_facts}"},
                  {"role":"user","content":prompt}],
        model="llama-3.1-8b-instant"
    )
    return response.choices[0].message.content.strip()

def extract_task_from_message(message):
    prompt = f"Determine if this message contains a task. Return only the task or NONE.\nMessage:\n{message}"
    response = groq_client.chat.completions.create(
        messages=[{"role":"system","content":"Extract tasks."},{"role":"user","content":prompt}],
        model="llama-3.1-8b-instant"
    )
    return response.choices[0].message.content.strip()

# -----------------------------
# AUTONOMOUS PROBLEM SOLVING
# -----------------------------
def solve_task(task):
    task_id, description, status, attempts, max_attempts, alternatives_json = task
    alternatives = json.loads(alternatives_json) if alternatives_json else []
    
    try:
        result = ask_groq(f"Attempt to complete this task autonomously: {description}", "")
        if "cannot" in result.lower() or "unable" in result.lower():
            alt_prompt = f"Task: {description}\nI couldn't do it. Suggest alternative ways to complete it."
            alt_result = ask_groq(alt_prompt,"")
            alternatives.append(alt_result)
            update_task_alternatives(task_id, alternatives)
            increment_task_attempts(task_id)
            for alt in alternatives:
                alt_try = ask_groq(f"Try to complete this alternative autonomously: {alt}","")
                if "cannot" not in alt_try.lower() and "unable" not in alt_try.lower():
                    mark_task_done(task_id)
                    send_whatsapp_message(YOUR_NUMBER,f"✅ Task completed autonomously: {alt}")
                    return
            if attempts+1 >= max_attempts:
                mark_task_done(task_id)
                send_whatsapp_message(YOUR_NUMBER,f"⚠️ Task failed after trying all alternatives: {description}")
        else:
            mark_task_done(task_id)
            send_whatsapp_message(YOUR_NUMBER,f"✅ Task completed autonomously: {description}")
    except Exception as e:
        send_whatsapp_message(YOUR_NUMBER,f"⚠️ Error while solving task {description}: {e}")

def run_autonomous_tasks():
    tasks = get_pending_tasks(YOUR_NUMBER)
    for task in tasks:
        solve_task(task)

# -----------------------------
# DAILY UPDATES
# -----------------------------
def jarvis_daily_updates():
    now = datetime.now()
    if now.hour == 5 and now.minute == 0:
        message = "🌅 Good morning!\n\n📋 Tasks for today:\n"
        tasks_text = "\n".join([f"• {t[1]}" for t in get_pending_tasks(YOUR_NUMBER)])
        message += tasks_text + "\n\n"

        cursor.execute("SELECT interest,level FROM interests WHERE user_id=%s ORDER BY level DESC",(YOUR_NUMBER,))
        interests = cursor.fetchall()
        for interest,level in interests:
            if level < 2: continue
            news = google_search(f"{interest} news",num_results=min(level,4))
            message += f"📰 Top {interest} news:\n{news}\n\n"

        send_whatsapp_message(YOUR_NUMBER,message.strip())
    if now.hour == 22 and now.minute == 0:
        message = "🌙 Nightly update:\n\n"
        cursor.execute("SELECT description FROM tasks WHERE user_id=%s AND status='done'",(YOUR_NUMBER,))
        completed = cursor.fetchall()
        pending = get_pending_tasks(YOUR_NUMBER)
        message += f"✅ Completed tasks: {len(completed) if completed else 0}\n"
        message += f"⏳ Pending tasks: {len(pending)}\n"
        send_whatsapp_message(YOUR_NUMBER,message.strip())

    run_autonomous_tasks()

# -----------------------------
# WHATSAPP WEBHOOK (TEXT + IMAGE)
# -----------------------------
@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    data = request.form
    user_id = data.get("From")
    user_message = data.get("Body","")
    media_url = data.get("MediaUrl0")
    media_type = data.get("MediaContentType0")

    if not user_id:
        return "OK",200

    # -----------------------------
    # Step 1: Image OCR
    # -----------------------------
    if media_url and media_type and media_type.startswith("image"):
        try:
            img_path = "temp_image.jpg"
            resp = requests.get(media_url)
            if resp.status_code == 200:
                with open(img_path,"wb") as f:
                    f.write(resp.content)
                ocr_text = pytesseract.image_to_string(Image.open(img_path)).strip()
                user_message += f"\n{ocr_text}"
        except Exception as e:
            send_whatsapp_message(user_id,f"⚠️ Could not process image: {e}")

    # -----------------------------
    # Memory & Profile
    # -----------------------------
    chat_history = get_memory(user_id)
    profile_facts = get_profile(user_id)
    updated_facts = extract_facts(profile_facts,user_message)
    update_profile(user_id,updated_facts)

    # -----------------------------
    # Tasks & Interests
    # -----------------------------
    task_text = extract_task_from_message(user_message)
    if task_text and task_text.upper()!="NONE":
        add_task(user_id,task_text)

    interests = extract_interests(user_message)
    update_interests(user_id,interests)

    # -----------------------------
    # Smart Keyword Search
    # -----------------------------
    search_keywords = ["search","look up","find","tell me about"]
    user_lower = user_message.lower().strip()
    if any(user_lower.startswith(k) for k in search_keywords) and len(user_lower.split())>2:
        result = google_search(user_message)
        resp = MessagingResponse()
        resp.message(result)
        return str(resp)

    # -----------------------------
    # Default AI Response
    # -----------------------------
    prompt = f"Chat history:\n{chat_history}\nUser: {user_message}\nJarvis:"
    ai_response = ask_groq(prompt,updated_facts)
    new_history = f"{chat_history}\nUser: {user_message}\nJarvis: {ai_response}"
    update_memory(user_id,new_history)

    resp = MessagingResponse()
    resp.message(ai_response)
    return str(resp)

# -----------------------------
# TEST ROUTE
# -----------------------------
@app.route("/test-send")
def test_send():
    send_whatsapp_message(YOUR_NUMBER,"Jarvis online ✅")
    return "Sent!"

# -----------------------------
# SCHEDULER
# -----------------------------
scheduler = BackgroundScheduler()
scheduler.add_job(jarvis_daily_updates,"interval",minutes=1)
scheduler.start()

# -----------------------------
# RUN APP
# -----------------------------
if __name__=="__main__":
    port=int(os.environ.get("PORT",8080))
    app.run(host="0.0.0.0",port=port)
