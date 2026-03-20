print("🚀 VERSION 6.2 (CRASH-PROOF BUILD)")

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
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")  # 🔥 FIXED

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
# QUERY AI SAFE
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
"""

        r = groq.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a smart assistant."},
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

        reply = ask(msg, memory, hints)

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
