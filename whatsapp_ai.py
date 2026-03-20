print("🚀 VERSION 6.1 (RAILWAY SAFE + ADAPTIVE AI)")

import os
import psycopg2
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from groq import Groq
import requests

# =============================
# CONFIG
# =============================
DATABASE_URL = os.environ.get("DATABASE_URL")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

SUPABASE_FUNCTION_URL = "https://creaavsrhfxwshknjghh.supabase.co/functions/v1/query_ai"
SUPABASE_ANON_KEY = "YOUR_SUPABASE_ANON_KEY"

TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")

# =============================
# DB
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
# CLIENTS
# =============================
groq = Groq(api_key=GROQ_API_KEY)
twilio = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
app = Flask(__name__)

# =============================
# PERSONALITY
# =============================
PERSONALITY = """
You are Jarvis — calm, intelligent, efficient, and helpful.

RULES:
- NEVER make up facts
- ONLY use given info
- If unsure, say you don’t know
- Keep responses short
- Do not ask unnecessary questions
"""

# =============================
# QUERY AI
# =============================
def get_query_hints(user_message):
    try:
        r = requests.post(
            SUPABASE_FUNCTION_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
            },
            json={"question": user_message}
        )
        return r.json().get("hints", [])
    except Exception as e:
        print("Query AI Error:", e)
        return []

# =============================
# ADAPTIVE MEMORY
# =============================
def get_recent_memory(uid, user_message):
    r = run_query(
        "SELECT chat_history FROM memory WHERE user_id=%s",
        (uid,),
        True
    )

    if not r:
        return ""

    lines = r[0][0].split("\n")
    msg = user_message.lower()

    reference_words = ["that", "it", "this", "before", "earlier", "what about", "you said"]

    if any(w in msg for w in reference_words):
        return "\n".join(lines[-12:])
    else:
        return "\n".join(lines[-4:])

# =============================
# ASK AI
# =============================
def ask(user_message, memory_context, hints):
    try:
        hint_text = "\n".join(hints)

        prompt = f"""
User message:
{user_message}

Conversation:
{memory_context}

Relevant context:
{hint_text}

Respond naturally and concisely.

Rules:
- No hallucination
- Keep it short
- No unnecessary questions
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
# MEMORY SAVE
# =============================
def update_memory(uid, text):
    run_query("""
        INSERT INTO memory(user_id, chat_history)
        VALUES (%s,%s)
        ON CONFLICT(user_id)
        DO UPDATE SET chat_history = memory.chat_history || %s
    """, (uid, text, text))

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
        memory_context = get_recent_memory(uid, msg)

        reply = ask(msg, memory_context, hints)

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
