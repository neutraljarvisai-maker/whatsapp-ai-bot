print("🚀 VERSION 9 (JARVIS + CLEAN CALENDAR + PERSONALITY)")

import os
import json
import psycopg2
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import requests

# =============================
# SAFE INIT
# =============================
DATABASE_URL = os.environ.get("DATABASE_URL")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

SUPABASE_FUNCTION_URL = "https://creaavsrhfxwshknjghh.supabase.co/functions/v1/query_ai"
SUPABASE_ANON_KEY = os.environ.get("YOUR_SUPABASE_ANON_KEY")

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")

GOOGLE_SERVICE_JSON = os.environ.get("GOOGLE_SERVICE_JSON")
MAIN_CALENDAR_ID = os.environ.get("MAIN_CALENDAR_ID", "primary")

# =============================
# PERSONALITY
# =============================
PERSONALITY = """
You are Jarvis — calm, intelligent, efficient, and helpful.

CRITICAL RULES:
- NEVER make up facts or events.
- ONLY use provided information.
- If unsure, say: "I don't have that information yet."

BEHAVIOR:
- Keep responses short and clear.
- Do NOT ask unnecessary questions.
- If user is unsure, suggest next step instead of repeating.
- If you added a calendar event, just confirm it briefly. Do NOT ask for more details.

STYLE:
- Smart, minimal, slightly witty.
- Talk like Jarvis from Iron Man — confident and concise.
"""

# =============================
# SAFE CLIENTS
# =============================
try:
    from groq import Groq
    groq = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
except Exception as e:
    print("Groq init failed:", e)
    groq = None

try:
    twilio = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
except Exception as e:
    print("Twilio init failed:", e)
    twilio = None

app = Flask(__name__)

# =============================
# GOOGLE CALENDAR (SERVICE ACCOUNT)
# =============================
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from datetime import datetime, timedelta
    from dateutil import parser as dateparser

    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    def get_calendar_service():
        try:
            if not GOOGLE_SERVICE_JSON:
                print("No GOOGLE_SERVICE_JSON found.")
                return None
            service_info = json.loads(GOOGLE_SERVICE_JSON)
            creds = service_account.Credentials.from_service_account_info(
                service_info, scopes=SCOPES
            )
            return build("calendar", "v3", credentials=creds)
        except Exception as e:
            print("Calendar service error:", e)
            return None

    def create_event(title, dt_str):
        try:
            service = get_calendar_service()
            if not service:
                return None

            dt = dateparser.parse(dt_str, fuzzy=True)
            if not dt:
                return None

            event = {
                "summary": title,
                "start": {
                    "dateTime": dt.isoformat(),
                    "timeZone": "Asia/Kolkata"
                },
                "end": {
                    "dateTime": (dt + timedelta(hours=1)).isoformat(),
                    "timeZone": "Asia/Kolkata"
                },
            }

            service.events().insert(calendarId=MAIN_CALENDAR_ID, body=event).execute()
            return f"📅 Done — *{title}* added to your calendar."
        except Exception as e:
            print("Calendar create_event error:", e)
            return None

except Exception as e:
    print("Google Calendar import failed:", e)
    def create_event(title, dt_str):
        return None

# =============================
# DB SAFE
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
# QUERY AI
# =============================
def get_query_hints(user_message):
    if not SUPABASE_ANON_KEY:
        return []
    try:
        r = requests.post(
            SUPABASE_FUNCTION_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
            },
            json={"question": user_message},
            timeout=5
        )
        return r.json().get("hints", [])
    except Exception as e:
        print("Query AI Error:", e)
        return []

# =============================
# MEMORY
# =============================
def get_recent_memory(uid, user_message):
    try:
        r = run_query(
            "SELECT chat_history FROM memory WHERE user_id=%s",
            (uid,),
            True
        )
        if not r:
            return ""
        lines = r[0][0].split("\n")
        msg = user_message.lower()
        ref_words = ["that", "it", "this", "before", "earlier", "you said"]
        if any(w in msg for w in ref_words):
            return "\n".join(lines[-10:])
        else:
            return "\n".join(lines[-4:])
    except:
        return ""

def get_profile(uid):
    r = run_query("SELECT facts FROM profile_memory WHERE user_id=%s", (uid,), True)
    return r[0][0] if r else ""

# =============================
# SMART EVENT DETECTION
# Returns dict with title + datetime, or None
# =============================
def detect_event(text):
    if not groq:
        return None

    try:
        r = groq.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """If the user wants to schedule an event, meeting, or reminder, extract:
- A short clean title (e.g. "Meeting", "Doctor Appointment", "Gym")
- The date and time as a string (e.g. "tomorrow at 10am", "March 21 at 3pm")

Respond ONLY in this exact format:
TITLE: <title>
DATETIME: <datetime string>

If no event is mentioned, respond with exactly: NONE"""
                },
                {"role": "user", "content": text}
            ],
            model="llama-3.1-8b-instant"
        )

        out = r.choices[0].message.content.strip()

        if "NONE" in out.upper() or "TITLE:" not in out:
            return None

        lines = out.split("\n")
        title = ""
        dt_str = ""
        for line in lines:
            if line.startswith("TITLE:"):
                title = line.replace("TITLE:", "").strip()
            if line.startswith("DATETIME:"):
                dt_str = line.replace("DATETIME:", "").strip()

        if title and dt_str:
            return {"title": title, "datetime": dt_str}
        return None

    except:
        return None

# =============================
# AI RESPONSE
# =============================
def ask(user_message, memory_context, hints, facts=""):
    if not groq:
        return "⚠️ AI not configured."

    try:
        hint_text = "\n".join(hints)

        prompt = f"""
User message:
{user_message}

Conversation context:
{memory_context}

Relevant memory hints:
{hint_text}

User profile:
{facts}

Respond naturally and concisely.
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
# SAVE MEMORY
# =============================
def update_memory(uid, text):
    try:
        run_query("""
            INSERT INTO memory(user_id, chat_history)
            VALUES (%s,%s)
            ON CONFLICT(user_id)
            DO UPDATE SET chat_history = memory.chat_history || %s
        """, (uid, text, text))
    except:
        pass

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

        hints = get_query_hints(msg)
        memory = get_recent_memory(uid, msg)
        facts = get_profile(uid)

        # Detect and create calendar event with clean title
        event = detect_event(msg)
        calendar_msg = None

        if event:
            calendar_msg = create_event(event["title"], event["datetime"])

        reply = ask(msg, memory, hints, facts)

        # If calendar event was added, replace reply with clean confirmation
        if calendar_msg:
            reply = calendar_msg

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
