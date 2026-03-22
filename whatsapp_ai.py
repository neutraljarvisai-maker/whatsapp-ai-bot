print("🚀 VERSION 16 (JARVIS + SMART PROFILE FIELD SELECTION)")

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
- ONLY use what is explicitly provided in context, profile, or hints.

BEHAVIOR:
- Use the user's profile naturally — if you know their name, use it.
- Be genuinely personal — reference what you know about them when relevant.
- Keep responses short and clear.
- Do NOT ask unnecessary questions.
- Do NOT assume details that weren't stated.

STYLE:
- Smart, minimal, slightly witty.
- Talk like Jarvis from Iron Man — confident and concise.
- Feel like you genuinely know this person.
"""

# =============================
# ALL PROFILE COLUMNS
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

# Always include these regardless of topic
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
# CONVERSATIONS (RECENT CHAT)
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
# SMART PROFILE FIELD SELECTOR
# Picks only relevant fields using a tiny Groq call
# =============================
def select_relevant_fields(user_message, intent):
    # For RECALL always return all filled fields
    if intent == "RECALL":
        return None  # None = load all

    if not groq:
        return ALWAYS_INCLUDE

    try:
        columns_str = ", ".join(PROFILE_COLUMNS)

        r = groq.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a profile field selector. Given a user message, return ONLY the most relevant field names from this list that would help answer it:

{columns_str}

Rules:
- Return maximum 8 fields
- Always include: name, communication_style
- Return as comma separated list only, nothing else
- If general chat, just return: name, communication_style, personality"""
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            model="llama-3.1-8b-instant",
            max_tokens=60
        )

        out = r.choices[0].message.content.strip()
        fields = [f.strip() for f in out.split(",") if f.strip() in PROFILE_COLUMNS]

        # Always add the always_include fields
        for f in ALWAYS_INCLUDE:
            if f not in fields:
                fields.append(f)

        return fields if fields else ALWAYS_INCLUDE

    except Exception as e:
        print("Field selector error:", e)
        return ALWAYS_INCLUDE

# =============================
# PROFILE — LOAD (SMART)
# =============================
def load_profile(uid, fields=None):
    try:
        if fields is None:
            # Load all filled fields
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
        else:
            # Load only specific fields
            safe_fields = [f for f in fields if f in PROFILE_COLUMNS]
            if not safe_fields:
                return {}
            select_cols = ", ".join(safe_fields)
            r = run_query(
                f"SELECT {select_cols} FROM profile WHERE user_id=%s",
                (uid,), True
            )
            if not r:
                return {}
            row = r[0]
            profile = {}
            for i, col in enumerate(safe_fields):
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
# PROFILE — FACT EXTRACTOR
# Runs silently after every message
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
                    "content": f"""You are a fact extractor. Extract NEW facts about the user from this conversation to save to their profile.

Current profile:
{profile_summary if profile_summary else "Empty"}

Available fields:
{', '.join(PROFILE_COLUMNS)}

Rules:
- Only extract facts that are NEW or UPDATE existing info
- Be concise — short phrases only
- Only facts about the USER, not Jarvis
- If nothing new, return NONE
- Do NOT invent facts

Format (one per line):
field_name: value

Or if nothing new: NONE"""
                },
                {
                    "role": "user",
                    "content": f"User: {user_message}\nJarvis: {jarvis_reply}"
                }
            ],
            model="llama-3.1-8b-instant",
            max_tokens=200
        )

        out = r.choices[0].message.content.strip()

        if out.upper() == "NONE" or not out:
            return

        updates = {}
        for line in out.split("\n"):
            if ":" in line:
                parts = line.split(":", 1)
                field = parts[0].strip().lower().replace(" ", "_")
                value = parts[1].strip()
                if field in PROFILE_COLUMNS and value:
                    updates[field] = value

        if not updates:
            return

        cols = ", ".join(["user_id"] + list(updates.keys()))
        placeholders = ", ".join(["%s"] * (len(updates) + 1))
        update_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
        values = [uid] + list(updates.values()) + list(updates.values())

        query = f"""
            INSERT INTO profile ({cols})
            VALUES ({placeholders})
            ON CONFLICT(user_id)
            DO UPDATE SET {update_clause}
        """

        run_query(query, values)
        print(f"Profile updated: {updates}")

    except Exception as e:
        print("Fact extractor error:", e)

# =============================
# INTENT CLASSIFIER
# =============================
def classify_intent(user_message, recent_chat):
    if not groq:
        return "CHAT"

    try:
        r = groq.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """You are an intent classifier. Return ONLY one label:

CHAT       — casual conversation, greetings, small talk
QUESTION   — asking for information, facts, or advice
ADD_EVENT  — user wants to CREATE or SCHEDULE a new event, meeting, or reminder
ADD_TASK   — user wants to add or track a task or to-do
ADD_GOAL   — user wants to set or track a goal
RECALL     — user is ASKING ABOUT or CHECKING existing schedule, past events, or memory

Examples:
"schedule a meeting tomorrow at 3" → ADD_EVENT
"add a reminder at 5pm" → ADD_EVENT
"can you set up a meeting today from 3 to 4" → ADD_EVENT
"what meetings do I have today" → RECALL
"did I have a meeting yesterday" → RECALL
"check my calendar" → RECALL
"hello" → CHAT
"what is photosynthesis" → QUESTION
"what's my name" → RECALL

Return ONLY the label."""
                },
                {
                    "role": "user",
                    "content": f"Recent context:\n{recent_chat}\n\nMessage: {user_message}"
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
# EVENT EXTRACTOR
# =============================
def extract_event(user_message, recent_chat):
    if not groq:
        return None

    try:
        r = groq.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """Extract event details from the conversation.

Generate a smart descriptive title based on context.
Look through entire context to find time/date even if mentioned earlier.
NEVER return "Not specified" — always make a best guess.
If no date: use "today". If no time: use "12:00 PM".

Respond ONLY in this format:
TITLE: <smart title>
DATETIME: <datetime string>"""
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
                    "content": """You are Jarvis. Answer using ONLY the data provided.
DO NOT invent any names, events, or details.
If the answer is not in the data, say: "I don't have that information."
Be short and direct."""
                },
                {
                    "role": "user",
                    "content": f"""User asked: {user_message}

User profile:
{profile_text}

Upcoming calendar events:
{events_text}

Recent conversation:
{recent_chat}

Memory hints:
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

        prompt = f"""
User message: {user_message}

User profile:
{profile_text if profile_text else "No profile data yet."}

Recent conversation:
{recent_chat}

Memory hints:
{" ".join(hints)}

Respond naturally and concisely.
IMPORTANT: Only use information provided. Do NOT invent anything.
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

        # Load recent chat
        recent_chat = get_recent_chat(uid, msg)
        hints = get_query_hints(msg)

        # Classify intent first
        intent = classify_intent(msg, recent_chat)
        print(f"Intent: {intent}")

        # Select only relevant profile fields (smart, cheap)
        relevant_fields = select_relevant_fields(msg, intent)
        profile = load_profile(uid, fields=relevant_fields)

        # Route
        if intent == "ADD_EVENT":
            event = extract_event(msg, recent_chat)
            if event:
                result = create_and_verify_event(event["title"], event["datetime"])
                reply = result if result else "⚠️ Couldn't add the event. Try again."
            else:
                reply = "I couldn't figure out the event details. Could you be more specific?"

        elif intent == "RECALL":
            # For recall, load full profile
            full_profile = load_profile(uid, fields=None)
            reply = handle_recall(msg, recent_chat, hints, full_profile)

        else:
            reply = ask(msg, recent_chat, hints, profile)

        # Save recent chat
        update_recent_chat(uid, f"\nUser: {msg}\nJarvis: {reply}")

        # Silently extract and save facts (use full profile for context)
        full_profile_for_extraction = load_profile(uid, fields=None)
        extract_and_save_facts(uid, msg, reply, full_profile_for_extraction)

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
