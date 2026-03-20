print("🚀 VERSION 11 (JARVIS + INTENT CLASSIFIER)")

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
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
except Exception as e:
    print("Twilio init failed:", e)
    twilio_client = None

app = Flask(__name__)

# =============================
# GOOGLE CALENDAR (SERVICE ACCOUNT)
# =============================
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from datetime import datetime, timedelta
    from dateutil import parser as dateparser
    import pytz

    SCOPES = ["https://www.googleapis.com/auth/calendar"]
    IST = pytz.timezone("Asia/Kolkata")

    def get_calendar_service():
        try:
            if not GOOGLE_SERVICE_JSON:
                return None
            service_info = json.loads(GOOGLE_SERVICE_JSON)
            creds = service_account.Credentials.from_service_account_info(
                service_info, scopes=SCOPES
            )
            return build("calendar", "v3", credentials=creds)
        except Exception as e:
            print("Calendar service error:", e)
            return None

    def create_and_verify_event(title, dt_str):
        try:
            service = get_calendar_service()
            if not service:
                return None

            dt = dateparser.parse(dt_str, fuzzy=True)
            if not dt:
                return "⚠️ Couldn't understand the date/time."

            if dt.tzinfo is None:
                dt = IST.localize(dt)

            end_dt = dt + timedelta(hours=1)

            event_body = {
                "summary": title,
                "start": {"dateTime": dt.isoformat(), "timeZone": "Asia/Kolkata"},
                "end": {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Kolkata"},
            }

            # Create
            created = service.events().insert(
                calendarId=MAIN_CALENDAR_ID, body=event_body
            ).execute()
            event_id = created.get("id")

            # Verify
            verified = service.events().get(
                calendarId=MAIN_CALENDAR_ID, eventId=event_id
            ).execute()

            saved_title = verified.get("summary", "")
            saved_start = verified.get("start", {}).get("dateTime", "")

            needs_fix = False
            if saved_title != title:
                needs_fix = True
            if saved_start:
                saved_dt = dateparser.parse(saved_start)
                if abs((saved_dt.replace(tzinfo=None) - dt.replace(tzinfo=None)).total_seconds()) > 60:
                    needs_fix = True

            # Fix if needed
            if needs_fix:
                service.events().update(
                    calendarId=MAIN_CALENDAR_ID, eventId=event_id, body=event_body
                ).execute()
                fix_note = " *(auto-corrected ✓)*"
            else:
                fix_note = ""

            display_dt = dt.strftime("%A, %d %B at %I:%M %p")
            return f"📅 *{title}*\n🕐 {display_dt}{fix_note}\n✅ Verified & saved."

        except Exception as e:
            print("Calendar error:", e)
            return None

except Exception as e:
    print("Google Calendar import failed:", e)
    def create_and_verify_event(title, dt_str):
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
            (uid,), True
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
# STAGE 1 — INTENT CLASSIFIER
# =============================
def classify_intent(user_message, memory_context):
    """
    Returns one of:
    CHAT | QUESTION | ADD_EVENT | ADD_TASK | ADD_GOAL | RECALL
    """
    if not groq:
        return "CHAT"

    try:
        r = groq.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """You are an intent classifier. Read the user's message and recent context and return ONLY one label:

CHAT       — casual conversation, greetings, small talk
QUESTION   — asking for information, facts, or advice
ADD_EVENT  — user clearly wants to schedule, add, or set a reminder/meeting/event
ADD_TASK   — user wants to add or track a task or to-do
ADD_GOAL   — user wants to set or track a goal
RECALL     — user is asking about something from their past conversations or memory

Rules:
- Only return ADD_EVENT if the user clearly wants to CREATE something on their calendar
- Asking ABOUT time or schedule = QUESTION, not ADD_EVENT
- Return ONLY the label, nothing else"""
                },
                {
                    "role": "user",
                    "content": f"Recent context:\n{memory_context}\n\nMessage: {user_message}"
                }
            ],
            model="llama-3.1-8b-instant",
            max_tokens=10
        )

        intent = r.choices[0].message.content.strip().upper()

        valid = ["CHAT", "QUESTION", "ADD_EVENT", "ADD_TASK", "ADD_GOAL", "RECALL"]
        return intent if intent in valid else "CHAT"

    except Exception as e:
        print("Intent classifier error:", e)
        return "CHAT"

# =============================
# STAGE 2 — EVENT EXTRACTOR
# =============================
def extract_event(user_message, memory_context):
    """Only called when intent is ADD_EVENT"""
    if not groq:
        return None

    try:
        r = groq.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """Extract the event details from the user's message.

Generate a smart descriptive title based on context (e.g. "Chemistry Exam Prep", "Doctor Checkup", "Team Standup") — NOT generic like "Meeting" or "Reminder".

Respond ONLY in this exact format:
TITLE: <smart title>
DATETIME: <datetime string>"""
                },
                {
                    "role": "user",
                    "content": f"Context: {memory_context}\n\nMessage: {user_message}"
                }
            ],
            model="llama-3.1-8b-instant"
        )

        out = r.choices[0].message.content.strip()
        title = ""
        dt_str = ""

        for line in out.split("\n"):
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
# STAGE 3 — AI RESPONSE
# =============================
def ask(user_message, memory_context, hints, facts=""):
    if not groq:
        return "⚠️ AI not configured."

    try:
        prompt = f"""
User message:
{user_message}

Conversation context:
{memory_context}

Relevant memory hints:
{" ".join(hints)}

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

        # Load context
        memory = get_recent_memory(uid, msg)
        hints = get_query_hints(msg)
        facts = get_profile(uid)

        # ── STAGE 1: Classify intent ──
        intent = classify_intent(msg, memory)
        print(f"Intent: {intent}")

        reply = ""

        # ── STAGE 2: Route to handler ──

        if intent == "ADD_EVENT":
            event = extract_event(msg, memory)
            if event:
                result = create_and_verify_event(event["title"], event["datetime"])
                reply = result if result else "⚠️ Couldn't add the event. Try again."
            else:
                reply = "I couldn't figure out the event details. Could you be more specific?"

        else:
            # CHAT, QUESTION, RECALL, ADD_TASK, ADD_GOAL all go to normal AI for now
            reply = ask(msg, memory, hints, facts)

        # Save to memory
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
