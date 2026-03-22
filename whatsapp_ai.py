print("🚀 VERSION 18 (JARVIS + CORRECT DATETIME + NO CONFIDENT WRONG ANSWERS)")

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
You are Jarvis — calm, intelligent, efficient, and deeply personal.

ABSOLUTE RULES — NEVER BREAK THESE:
- NEVER invent names, people, places, events, or details not given to you.
- NEVER fill in gaps with guesses. If you don't know, say: "I don't have that information."
- ONLY use what is explicitly in the profile, context, or hints.
- NEVER reference the conversation history awkwardly or robotically.
- If the user corrects you — accept it immediately and simply. Do NOT double down or justify wrong info.

BEHAVIOR:
- Use the user's name naturally if you know it.
- Keep responses SHORT and direct — 1 to 3 sentences max for casual chat.
- Do NOT ask unnecessary questions.
- Do NOT over-explain or pad responses.
- Do NOT say things like "I remember our last interaction" or "You said X earlier."
- If corrected, just say "You're right" and move on. Never argue.

STYLE:
- Smart, minimal, slightly witty.
- Talk like Jarvis from Iron Man — confident and concise.
- Never sound like a customer service bot.
"""

# =============================
# PROFILE COLUMNS
# =============================
PROFILE_COLUMNS = [
    "name", "age", "birthday", "gender", "location", "nationality", "languages", "religion",
    "school", "grade", "subjects", "favourite_subject", "worst_subject", "exam_dates",
    "academic_goals", "academic_struggles", "study_style",
    "dream_job", "career_goals", "skills_building", "entrepreneurial_ideas", "long_term_vision",
    "active_projects", "project_details", "project_deadlines", "project_collaborators",
    "project_history", "idea_pipeline", "current_focus", "wins_achievements",
    "short_term_goals", "long_term_goals", "life_goals", "obstacles_to_goals",
    "friends", "best_friend", "family", "romantic_life", "social_circle", "recurring_people",
    "personality", "communication_style", "emotional_patterns", "humor", "fears",
    "motivations", "life_philosophy",
    "daily_routine", "energy_patterns", "time_relationship", "health", "hobbies",
    "creativity", "digital_life", "money_mindset", "food_lifestyle", "travel",
    "personal_history", "dreams", "regrets_lessons", "opinions", "social_dynamics",
    "spirituality", "ambition_level", "observed_behaviours", "unspoken_rules",
    "spontaneous_revelations", "physical_world", "relationship_with_tech",
    "language_expression", "self_awareness", "stress_response", "decision_making",
    "identity", "world_view", "future_self",
    "work_style", "technical_skills", "creative_skills", "problem_solving",
    "tools_workflow", "collaboration_style", "learning_style", "resources"
]

ALWAYS_INCLUDE = ["name", "communication_style", "personality"]

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

    SCOPES = ["https://www.googleapis.com/auth/calendar"]

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

    def get_upcoming_events():
        try:
            service = get_calendar_service()
            if not service:
                return []
            now = datetime.utcnow().isoformat() + "Z"
            result = service.events().list(
                calendarId=MAIN_CALENDAR_ID,
                timeMin=now,
                maxResults=5,
                singleEvents=True,
                orderBy="startTime"
            ).execute()
            events = result.get("items", [])
            if not events:
                return []
            formatted = []
            for e in events:
                title = e.get("summary", "Untitled")
                start = e.get("start", {}).get("dateTime", e.get("start", {}).get("date", ""))
                if start:
                    try:
                        dt = dateparser.parse(start)
                        display = dt.strftime("%A, %d %B at %I:%M %p")
                    except:
                        display = start
                formatted.append(f"• {title} — {display}")
            return formatted
        except Exception as e:
            print("get_upcoming_events error:", e)
            return []

    def create_and_verify_event(title, dt_str):
        try:
            service = get_calendar_service()
            if not service:
                return None
            dt = dateparser.parse(dt_str, fuzzy=True)
            if not dt:
                return "⚠️ Couldn't understand the date/time."
            end_dt = dt + timedelta(hours=1)
            event_body = {
                "summary": title,
                "start": {"dateTime": dt.isoformat(), "timeZone": "Asia/Kolkata"},
                "end": {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Kolkata"},
            }
            created = service.events().insert(
                calendarId=MAIN_CALENDAR_ID, body=event_body
            ).execute()
            event_id = created.get("id")
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
    def get_upcoming_events():
        return []
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
# QUERY AI (SUPABASE)
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
# CONVERSATIONS
# =============================
def get_recent_chat(uid, user_message):
    try:
        r = run_query(
            "SELECT recent_chat FROM conversations WHERE user_id=%s",
            (uid,), True
        )
        if not r or not r[0][0]:
            return ""
        lines = r[0][0].split("\n")
        msg = user_message.lower()
        ref_words = ["that", "it", "this", "before", "earlier", "you said"]
        if any(w in msg for w in ref_words):
            return "\n".join(lines[-14:])
        else:
            return "\n".join(lines[-8:])
    except:
        return ""

def update_recent_chat(uid, text):
    try:
        run_query("""
            INSERT INTO conversations(user_id, recent_chat)
            VALUES (%s, %s)
            ON CONFLICT(user_id)
            DO UPDATE SET recent_chat = COALESCE(conversations.recent_chat, '') || %s
        """, (uid, text, text))
    except Exception as e:
        print("Chat update error:", e)

# =============================
# PROFILE — LOAD
# =============================
def load_profile(uid):
    try:
        r = run_query(
            "SELECT * FROM profile WHERE user_id=%s",
            (uid,), True
        )
        if not r:
            return {}
        cols = ["user_id"] + PROFILE_COLUMNS
        row = r[0]
        profile = {}
        for i, col in enumerate(cols):
            if i < len(row) and row[i]:
                profile[col] = row[i]
        return profile
    except Exception as e:
        print("Profile load error:", e)
        return {}

def format_profile(profile):
    if not profile:
        return ""
    lines = []
    for k, v in profile.items():
        if k != "user_id" and v:
            lines.append(f"{k.replace('_', ' ').title()}: {v}")
    return "\n".join(lines) if lines else ""

# =============================
# PROFILE — FACT EXTRACTOR (FIXED)
# =============================
def extract_and_save_facts(uid, user_message, jarvis_reply, current_profile):
    if not groq:
        return

    try:
        profile_summary = format_profile(current_profile)

        r = groq.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a fact extractor. Extract NEW facts about the user from this conversation.

Current profile:
{profile_summary if profile_summary else "Empty — extract anything useful"}

Available fields (use exact field names):
{', '.join(PROFILE_COLUMNS)}

Rules:
- Extract facts that are NEW or UPDATE existing info
- Short phrases only — no full sentences
- Only facts about the USER, not Jarvis
- If nothing new, return exactly: NONE
- Do NOT invent facts

Format — one per line:
field_name: value

Example:
name: Azlan
school: some school
active_projects: building a WhatsApp AI called Jarvis"""
                },
                {
                    "role": "user",
                    "content": f"User said: {user_message}\nJarvis replied: {jarvis_reply}"
                }
            ],
            model="llama-3.1-8b-instant",
            max_tokens=300
        )

        out = r.choices[0].message.content.strip()
        print(f"Fact extractor raw output: {out}")

        if out.upper().startswith("NONE"):
            return

        updates = {}
        for line in out.split("\n"):
            line = line.strip()
            if ":" in line:
                parts = line.split(":", 1)
                field = parts[0].strip().lower().replace(" ", "_").replace("-", "_")
                value = parts[1].strip()
                if field in PROFILE_COLUMNS and value and value.upper() != "NONE":
                    updates[field] = value

        if not updates:
            print("No valid facts extracted")
            return

        # Build safe upsert
        set_clause = ", ".join([f"{k} = EXCLUDED.{k}" for k in updates.keys()])
        cols = ", ".join(["user_id"] + list(updates.keys()))
        placeholders = ", ".join(["%s"] * (len(updates) + 1))
        values = [uid] + list(updates.values())

        query = f"""
            INSERT INTO profile ({cols})
            VALUES ({placeholders})
            ON CONFLICT(user_id)
            DO UPDATE SET {set_clause}
        """

        run_query(query, values)
        print(f"✅ Profile updated: {updates}")

    except Exception as e:
        print(f"Fact extractor error: {e}")

# =============================
# INTENT CLASSIFIER (IMPROVED)
# =============================
def classify_intent(user_message, recent_chat):
    if not groq:
        return "CHAT"

    try:
        r = groq.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """You are an intent classifier. Return ONLY one label.

Labels:
CHAT       — greetings, small talk, casual conversation
QUESTION   — asking for information, facts, explanations, or advice
ADD_EVENT  — user wants to CREATE or SCHEDULE something new (meeting, reminder, event)
ADD_TASK   — user wants to add a task or to-do item
ADD_GOAL   — user wants to set a goal
RECALL     — user is asking ABOUT their existing schedule, past info, or saved memory

Critical rules:
- If user says "add", "schedule", "set", "create", "book", "remind me", "put" + time/date → ADD_EVENT
- If user asks "what", "when", "do I have", "check my" → RECALL or QUESTION
- Simple "hi", "hello", "hey", "ok", "yes", "no" → CHAT
- "can you do a task" or vague requests → CHAT or QUESTION, NOT ADD_TASK

Examples:
"add a meeting today at 3pm" → ADD_EVENT
"meeting at 3pm" → ADD_EVENT
"schedule something for tomorrow" → ADD_EVENT
"what meetings do I have" → RECALL
"check my calendar" → RECALL
"hi" → CHAT
"can you do a task for me" → CHAT
"what is python" → QUESTION

Return ONLY the label, nothing else."""
                },
                {
                    "role": "user",
                    "content": f"Message: {user_message}"
                }
            ],
            model="llama-3.1-8b-instant",
            max_tokens=10
        )

        intent = r.choices[0].message.content.strip().upper()
        # Clean up in case model adds extra text
        for label in ["ADD_EVENT", "ADD_TASK", "ADD_GOAL", "RECALL", "QUESTION", "CHAT"]:
            if label in intent:
                print(f"Intent: {label}")
                return label
        print(f"Intent: CHAT (fallback from: {intent})")
        return "CHAT"

    except Exception as e:
        print("Intent classifier error:", e)
        return "CHAT"

# =============================
# EVENT EXTRACTOR (BETTER NAMING + REAL DATETIME)
# =============================
def extract_event(user_message, recent_chat, profile):
    if not groq:
        return None

    from datetime import datetime as dt_now
    current_dt = dt_now.now().strftime("%A, %d %B %Y, %I:%M %p")

    name = profile.get("name", "")
    active_projects = profile.get("active_projects", "")

    try:
        r = groq.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"""Extract event details from the user's message.

TODAY IS: {current_dt} (IST)
Use this as your reference for "today", "tomorrow", "tonight" etc.

User context:
- Name: {name if name else "unknown"}
- Active projects: {active_projects if active_projects else "none known"}

Generate a SMART, DESCRIPTIVE title — NOT generic names like "Meeting" or "Reminder".
Examples:
- "meeting with friends about school project" → "School Project Meetup"
- "doctor appointment tomorrow" → "Doctor Appointment"
- "study session at 4pm" → "Study Session"
- "meeting at 3pm" → "Afternoon Meeting"
- "meeting at 4pm" → "Evening Prep Meeting"

CRITICAL TIME RULES:
- Extract the EXACT time the user mentioned — do NOT change it
- "at 4pm" → 4:00 PM, NOT 12:00 PM
- "at 3pm" → 3:00 PM
- Only default to 12:00 PM if absolutely NO time was mentioned anywhere

Look through the full conversation for time/date even if mentioned earlier.
NEVER return "Not specified".
If no date: use today's actual date. If truly no time: use 12:00 PM.

Respond ONLY in this exact format:
TITLE: <smart title>
DATETIME: <full datetime e.g. "23 March 2026 at 4:00 PM">"""
                },
                {
                    "role": "user",
                    "content": f"Recent conversation:\n{recent_chat}\n\nLatest message: {user_message}"
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
# RECALL HANDLER
# =============================
def handle_recall(user_message, recent_chat, hints, profile):
    events = get_upcoming_events()
    events_text = "\n".join(events) if events else "No upcoming events found."
    profile_text = format_profile(profile)

    if not groq:
        return events_text

    try:
        r = groq.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """You are Jarvis. Answer using ONLY the data provided below.
DO NOT invent any names, events, or details.
If the answer is not in the data, say: "I don't have that information."
Be short and direct — 1 to 2 sentences max."""
                },
                {
                    "role": "user",
                    "content": f"""User asked: {user_message}

Profile:
{profile_text if profile_text else "No profile data yet."}

Upcoming events:
{events_text}

Recent conversation:
{recent_chat}

Hints:
{" ".join(hints)}"""
                }
            ],
            model="llama-3.1-8b-instant"
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        print("Recall handler error:", e)
        return events_text

# =============================
# NORMAL AI RESPONSE
# =============================
def ask(user_message, recent_chat, hints, profile):
    if not groq:
        return "⚠️ AI not configured."

    try:
        profile_text = format_profile(profile)

        prompt = f"""User message: {user_message}

Profile:
{profile_text if profile_text else "No profile data yet."}

Recent conversation:
{recent_chat}

Hints: {" ".join(hints)}

Reply naturally. Be short. Do NOT reference the conversation awkwardly."""

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
        recent_chat = get_recent_chat(uid, msg)
        hints = get_query_hints(msg)
        profile = load_profile(uid)

        # Classify intent
        intent = classify_intent(msg, recent_chat)

        # Route
        if intent == "ADD_EVENT":
            event = extract_event(msg, recent_chat, profile)
            if event:
                result = create_and_verify_event(event["title"], event["datetime"])
                reply = result if result else "⚠️ Couldn't add the event. Try again."
            else:
                reply = "I couldn't figure out the event details. Could you be more specific?"

        elif intent == "RECALL":
            reply = handle_recall(msg, recent_chat, hints, profile)

        else:
            reply = ask(msg, recent_chat, hints, profile)

        # Save chat
        update_recent_chat(uid, f"\nUser: {msg}\nJarvis: {reply}")

        # Silently extract and save facts
        extract_and_save_facts(uid, msg, reply, profile)

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
