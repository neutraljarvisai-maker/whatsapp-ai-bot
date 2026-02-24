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

# -----------------------------
# CONFIG
# -----------------------------
DATABASE_URL = os.environ.get("DATABASE_URL")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")

TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"
YOUR_NUMBER = os.environ.get("YOUR_NUMBER")

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")  # Your Google API Key
GOOGLE_CSE_ID = os.environ.get("GOOGLE_CSE_ID")    # Your Custom Search Engine ID

if not DATABASE_URL or not GROQ_API_KEY or not YOUR_NUMBER or not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
    raise ValueError("Please set all required environment variables (DATABASE_URL, GROQ_API_KEY, YOUR_NUMBER, GOOGLE_API_KEY, GOOGLE_CSE_ID)")

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
        task TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

print("Connected to database successfully!")

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
# SEND WHATSAPP MESSAGE
# -----------------------------
def send_whatsapp_message(to_number, message):
    twilio_client.messages.create(
        body=message,
        from_=TWILIO_WHATSAPP_NUMBER,
        to=to_number
    )

# -----------------------------
# TASK FUNCTIONS
# -----------------------------
def add_task(user_id, task):
    cursor.execute(
        "INSERT INTO tasks (user_id, task) VALUES (%s, %s)",
        (user_id, task)
    )

def get_tasks(user_id):
    cursor.execute(
        "SELECT task FROM tasks WHERE user_id=%s ORDER BY created_at",
        (user_id,)
    )
    rows = cursor.fetchall()
    if not rows:
        return "No tasks scheduled."
    return "\n".join([f"• {r[0]}" for r in rows])

def extract_task_from_message(message):
    prompt = f"""
Determine if this message contains a task or responsibility.

Message:
{message}

If YES → return ONLY the task in one short sentence.
If NO → return NONE.
"""
    response = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": "Extract tasks."},
            {"role": "user", "content": prompt}
        ],
        model="llama-3.1-8b-instant"
    )
    return response.choices[0].message.content.strip()

# -----------------------------
# INTEREST EXTRACTION
# -----------------------------
INTEREST_CATEGORIES = ["Sports", "Entertainment", "Tech", "Study", "Finance", "Cars"]

def extract_interests(message):
    prompt = f"""
Extract any personal interests from this message. Only use these categories: 
{', '.join(INTEREST_CATEGORIES)}

Return JSON ONLY like this:
{{ "interests": [{{"topic": "...", "level": 1-4}}] }}

Level guide:
1 = Casual mention
2 = Moderate interest
3 = Strong interest / repeated mentions
4 = Hardcore / extremely passionate

Message:
{message}
"""
    response = groq_client.chat.completions.create(
        messages=[{"role": "system", "content": "Extract user interests."},
                  {"role": "user", "content": prompt}],
        model="llama-3.1-8b-instant"
    )
    try:
        content = response.choices[0].message.content
        return json.loads(content)["interests"]
    except:
        return []

def update_interests(user_id, interests):
    for item in interests:
        topic = item["topic"].capitalize()
        level = max(1, min(4, item["level"]))
        cursor.execute("SELECT level FROM interests WHERE user_id=%s AND interest=%s",
                       (user_id, topic))
        existing = cursor.fetchone()
        if existing:
            new_level = max(existing[0], level)
            cursor.execute("UPDATE interests SET level=%s WHERE user_id=%s AND interest=%s",
                           (new_level, user_id, topic))
        else:
            cursor.execute("INSERT INTO interests (user_id, interest, level) VALUES (%s, %s, %s)",
                           (user_id, topic, level))

# -----------------------------
# GOOGLE SEARCH FUNCTION
# -----------------------------
def google_search(query, num_results=3):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": query,
        "num": num_results
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        items = data.get("items", [])
        if not items:
            return "I couldn't find anything useful for that."
        results_text = ""
        for i, item in enumerate(items, 1):
            title = item.get("title", "No title")
            snippet = item.get("snippet", "")
            link = item.get("link", "")
            results_text += f"{i}. {title}\n{snippet}\n{link}\n\n"
        return results_text.strip()
    except Exception as e:
        return f"Error fetching search results: {e}"

# -----------------------------
# DAILY UPDATES
# -----------------------------
def jarvis_daily_updates():
    now = datetime.now()
    
    # 🌅 Morning briefing (5 AM)
    if now.hour == 5 and now.minute == 0:
        # Tasks
        tasks = get_tasks(YOUR_NUMBER)
        message = f"🌅 Good morning.\n\n📋 Your tasks for today:\n{tasks}\n\n"

        # Fetch top interests
        cursor.execute("SELECT interest, level FROM interests WHERE user_id=%s ORDER BY level DESC", (YOUR_NUMBER,))
        interests = cursor.fetchall()

        # For each interest, fetch a Google search summary
        for interest, level in interests:
            # Limit number of results based on level (1-4)
            num_results = min(4, level)
            search_result = google_search(f"{interest} news", num_results=num_results)
            message += f"📰 Top {interest} news:\n{search_result}\n\n"

        send_whatsapp_message(YOUR_NUMBER, message.strip())

    # 🌙 Nightly update (10 PM)
    if now.hour == 22 and now.minute == 0:
        send_whatsapp_message(
            YOUR_NUMBER,
            "🌙 Nightly update: All systems running."
        )

# -----------------------------
# MEMORY FUNCTIONS
# -----------------------------
def get_memory(user_id):
    cursor.execute("SELECT chat_history FROM memory WHERE user_id=%s", (user_id,))
    row = cursor.fetchone()
    return row[0] if row else ""

def update_memory(user_id, chat_history):
    cursor.execute("""
        INSERT INTO memory(user_id, chat_history) VALUES (%s, %s)
        ON CONFLICT (user_id) DO UPDATE SET chat_history = EXCLUDED.chat_history
    """, (user_id, chat_history))

# -----------------------------
# PROFILE MEMORY
# -----------------------------
def get_profile(user_id):
    cursor.execute("SELECT facts FROM profile_memory WHERE user_id=%s", (user_id,))
    row = cursor.fetchone()
    return row[0] if row else ""

def update_profile(user_id, facts):
    cursor.execute("""
        INSERT INTO profile_memory(user_id, facts) VALUES (%s, %s)
        ON CONFLICT (user_id) DO UPDATE SET facts = EXCLUDED.facts
    """, (user_id, facts))

# -----------------------------
# FACT EXTRACTION
# -----------------------------
def extract_facts(old_facts, new_message):
    prompt = f"""
Existing facts:
{old_facts}

User message:
{new_message}

Extract important personal facts.
Return short bullet points.
"""
    response = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": "Extract user facts."},
            {"role": "user", "content": prompt}
        ],
        model="llama-3.1-8b-instant"
    )
    return response.choices[0].message.content.strip()

# -----------------------------
# ASK GROQ
# -----------------------------
def ask_groq(prompt, profile_facts):
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": f"You are Jarvis, a calm, intelligent AI assistant.\nKnown facts about the user:\n{profile_facts}"},
            {"role": "user", "content": prompt}
        ],
        model="llama-3.1-8b-instant"
    )
    return chat_completion.choices[0].message.content.strip()

# -----------------------------
# WHATSAPP WEBHOOK
# -----------------------------
@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    data = request.form
    user_id = data.get("From")
    user_message = data.get("Body")
    if not user_id or not user_message:
        return "OK", 200

    # Memory & Profile
    chat_history = get_memory(user_id)
    profile_facts = get_profile(user_id)
    updated_facts = extract_facts(profile_facts, user_message)
    update_profile(user_id, updated_facts)

    # Automatic Task Detection
    task = extract_task_from_message(user_message)
    if task and task.upper() != "NONE":
        add_task(user_id, task)

    # Automatic Interest Learning
    interests = extract_interests(user_message)
    update_interests(user_id, interests)

    # ⭐ Check if user wants a search
    search_keywords = ["search", "look up", "find", "tell me about"]
    if any(k in user_message.lower() for k in search_keywords):
        search_result = google_search(user_message)
        resp = MessagingResponse()
        resp.message(search_result)
        return str(resp)

    # AI Response
    prompt = f"Chat history:\n{chat_history}\nUser: {user_message}\nJarvis:"
    ai_response = ask_groq(prompt, updated_facts)

    # Update Memory
    new_history = f"{chat_history}\nUser: {user_message}\nJarvis: {ai_response}"
    update_memory(user_id, new_history)

    resp = MessagingResponse()
    resp.message(ai_response)
    return str(resp)

# -----------------------------
# TEST ROUTE
# -----------------------------
@app.route("/test-send")
def test_send():
    send_whatsapp_message(YOUR_NUMBER, "Jarvis online ✅")
    return "Sent!"

# -----------------------------
# START SCHEDULER
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

