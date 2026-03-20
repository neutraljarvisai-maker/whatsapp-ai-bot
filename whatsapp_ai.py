print("🚀 VERSION 7 (FULL JARVIS SAFE BUILD)")

import os
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
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")

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
# OPTIONAL: GOOGLE CALENDAR
# =============================
try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from datetime import datetime, timedelta
    from dateutil import parser

    TOKEN_FILE = "token.json"

    def get_calendar_service():
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE)
            return build("calendar", "v3", credentials=creds)
        except Exception as e:
            print("Calendar init error:", e)
            return None

    def create_event(text):
        try:
            service = get_calendar_service()
            if not service:
                return None

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
            return "📅 Event added to calendar."
        except Exception as e:
            print("Calendar error:", e)
            return None

except:
    def create_event(text):
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

# =============================
# SMART DETECTION (TASK / EVENT)
# =============================
def detect_event(text):
    if not groq:
        return None

    try:
        r = groq.chat.completions.create(
            messages=[
                {"role": "system", "content": "Extract event if user mentions scheduling. Else return NONE."},
                {"role": "user", "content": text}
            ],
            model="llama-3.1-8b-instant"
        )

        out = r.choices[0].message.content.strip()
        return None if "NONE" in out.upper() else out

    except:
        return None

# =============================
# AI RESPONSE
# =============================
def ask(user_message, memory_context, hints):
    if not groq:
        return "⚠️ AI not configured."

    try:
        prompt = f"""
User: {user_message}

Context:
{memory_context}

Hints:
{" ".join(hints)}

Rules:
- Be accurate
- Be short
- No guessing
- Don't ask unnecessary questions
"""

        r = groq.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are Jarvis, a smart assistant."},
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

        # 🔥 Detect event
        event = detect_event(msg)
        calendar_msg = None

        if event:
            calendar_msg = create_event(event)

        reply = ask(msg, memory, hints)

        if calendar_msg:
            reply += f"\n\n{calendar_msg}"

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
