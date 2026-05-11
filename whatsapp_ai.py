

print("🚀 VERSION 28 (JARVIS + CALENDAR FIX + NLU ROBUSTNESS)") # Version increment

import os
import json
import re
import psycopg2
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import requests
from datetime import datetime, timedelta, timezone # For time manipulations
import dateparser # For parsing various date/time formats
import logging # For better logging

# Load environment variables from .env file if running locally (Railway usually handles this)
# from dotenv import load_dotenv # Uncomment if you use .env for local development
# load_dotenv()

# =============================
# SAFE INIT / CONFIGURATIONS
# =============================
# Database credentials
DATABASE_URL = os.environ.get("DATABASE_URL")

# Groq API credentials
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Supabase for AI queries (if used - seems to be for hints)
SUPABASE_FUNCTION_URL = "https://creaavsrhfxwshknjghh.supabase.co/functions/v1/query_ai"
SUPABASE_ANON_KEY = os.environ.get("YOUR_SUPABASE_ANON_KEY") # Replace with actual env var name if different

# Twilio credentials
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER") # Not explicitly used in webhook but good to have

# Google Calendar API credentials
# GOOGLE_SERVICE_JSON needs to be the JSON content of your service account key as a string
GOOGLE_SERVICE_JSON = os.environ.get("GOOGLE_SERVICE_JSON")
MAIN_CALENDAR_ID = os.environ.get("MAIN_CALENDAR_ID", "primary") # Defaults to primary if not set

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# =============================
# PERSONALITY & PROFILE DEFINITIONS
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
# SAFE CLIENT INITIALIZATION
# =============================
groq = None
try:
    if GROQ_API_KEY:
        from groq import Groq
        groq = Groq(api_key=GROQ_API_KEY)
        logger.info("Groq client initialized.")
    else:
        logger.warning("GROQ_API_KEY not set. Groq LLM functionality will be unavailable.")
except ImportError:
    logger.error("Groq library not found. Please install it: pip install groq")
except Exception as e:
    logger.error(f"Groq client initialization failed: {e}")

twilio_client = None
try:
    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
        from twilio.rest import Client as TwilioClient
        twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        logger.info("Twilio client initialized.")
    else:
        logger.warning("TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN not set. Twilio functionality may be limited.")
except Exception as e:
    logger.error(f"Twilio client initialization failed: {e}")

app = Flask(__name__)

# =============================
# GOOGLE CALENDAR INTEGRATION (using Service Account JSON from env var)
# =============================
google_calendar_service = None
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from datetime import datetime, timedelta, timezone
    from dateutil import parser as dateparser # For parsing various date/time formats

    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    def get_calendar_service():
        """
        Authenticates using service account JSON from GOOGLE_SERVICE_JSON env var.
        Returns a Google Calendar API service object or None if authentication fails.
        """
        global google_calendar_service # Use the global service object
        if google_calendar_service:
            return google_calendar_service

        if not GOOGLE_SERVICE_JSON:
            logger.error("GOOGLE_SERVICE_JSON environment variable not set.")
            return None

        try:
            service_account_info = json.loads(GOOGLE_SERVICE_JSON)
            creds = service_account.Credentials.from_service_account_info(
                service_account_info, scopes=SCOPES
            )
            google_calendar_service = build("calendar", "v3", credentials=creds)
            logger.info("Google Calendar service initialized successfully.")
            return google_calendar_service
        except json.JSONDecodeError:
            logger.error("Failed to parse GOOGLE_SERVICE_JSON. Ensure it's valid JSON.")
            return None
        except Exception as e:
            logger.error(f"Error initializing Google Calendar service: {e}")
            return None

    def get_events_in_range(time_min, time_max):
        """Fetches and formats events within a specified time range."""
        service = get_calendar_service()
        if not service:
            return []

        try:
            result = service.events().list(
                calendarId=MAIN_CALENDAR_ID,
                timeMin=time_min.isoformat() + "Z",
                timeMax=time_max.isoformat() + "Z",
                maxResults=10,
                singleEvents=True,
                orderBy="startTime"
            ).execute()

            events = result.get("items", [])
            if not events:
                return []

            formatted_events = []
            for e in events:
                title = e.get("summary", "Untitled")
                start = e.get("start", {}).get("dateTime", e.get("start", {}).get("date", ""))
                if start:
                    try:
                        # Try to parse as dateTime first, then as date
                        if "T" in start:
                            dt = dateparser.parse(start)
                            display = dt.strftime("%A, %d %B at %I:%M %p")
                        else: # Date-only event
                            dt = dateparser.parse(start)
                            display = dt.strftime("%A, %d %B")
                    except Exception as parse_err:
                        logger.warning(f"Could not parse date '{start}': {parse_err}")
                        display = start # Fallback to raw string
                else:
                    display = "Time unknown"
                formatted_events.append(f"• {title} — {display}")
            return formatted_events
        except Exception as e:
            logger.error(f"Error fetching events in range: {e}")
            return []

    def get_upcoming_events():
        """Fetches upcoming events for the next 30 days."""
        now = datetime.utcnow()
        future = now + timedelta(days=30)
        return get_events_in_range(now, future)

    def get_events_for_query(user_message):
        """Determines the relevant time frame for event queries and fetches events."""
        from datetime import timezone, timedelta as td
        # Assume local time for parsing keywords like 'today', 'tomorrow'
        # Then convert to UTC for Google API. Defaulting to IST offset for parsing.
        try:
            ist = timezone(td(hours=5, minutes=30))
            now_ist = datetime.now(ist).replace(tzinfo=None) # Get current time in IST, naive for dateparser
        except Exception as tz_err:
            logger.warning(f"Could not determine IST timezone, defaulting to UTC for relative time parsing. Error: {tz_err}")
            now_ist = datetime.utcnow().replace(tzinfo=None) # Fallback to UTC

        msg_lower = user_message.lower()
        start_dt = None
        end_dt = None
        time_label = "today"

        if "yesterday" in msg_lower:
            start_dt = (now_ist - timedelta(days=1)).replace(hour=0, minute=0, second=0)
            end_dt = (now_ist - timedelta(days=1)).replace(hour=23, minute=59, second=59)
            time_label = "yesterday"
        elif "last week" in msg_lower:
            start_dt = (now_ist - timedelta(weeks=1)).replace(hour=0, minute=0, second=0)
            end_dt = now_ist # Up to current moment for 'last week'
            time_label = "last week"
        elif "tomorrow" in msg_lower:
            start_dt = (now_ist + timedelta(days=1)).replace(hour=0, minute=0, second=0)
            end_dt = (now_ist + timedelta(days=1)).replace(hour=23, minute=59, second=59)
            time_label = "tomorrow"
        elif "next week" in msg_lower:
            start_dt = now_ist.replace(hour=0, minute=0, second=0)
            end_dt = now_ist + timedelta(weeks=1)
            time_label = "next week"
        elif "this week" in msg_lower or "week" in msg_lower:
            start_dt = now_ist.replace(hour=0, minute=0, second=0)
            end_dt = now_ist + timedelta(days=7)
            time_label = "this week"
        else: # Default to today
            start_dt = now_ist.replace(hour=0, minute=0, second=0)
            end_dt = now_ist.replace(hour=23, minute=59, second=59)
            time_label = "today"

        # Convert determined IST times to UTC for Google Calendar API
        ist_offset_td = timedelta(hours=5, minutes=30) # IST offset
        start_utc = start_dt - ist_offset_td
        end_utc = end_dt - ist_offset_td

        events = get_events_in_range(start_utc, end_utc)
        return events, time_label

    def cancel_event(user_message, recent_chat, profile_name="user"):
        """
        Identifies an event to cancel from the user's upcoming events and deletes it.
        Uses LLM to determine which event if multiple are possible.
        """
        service = get_calendar_service()
        if not service:
            return "⚠️ Calendar service is unavailable. Please check configuration."

        try:
            now_utc = datetime.utcnow()
            future_utc = now_utc + timedelta(days=30) # Look for events in the next 30 days

            # Fetch upcoming events
            events_result = service.events().list(
                calendarId=MAIN_CALENDAR_ID,
                timeMin=now_utc.isoformat() + "Z",
                timeMax=future_utc.isoformat() + "Z",
                maxResults=10,
                singleEvents=True,
                orderBy="startTime"
            ).execute()
            events_raw = events_result.get("items", [])

            if not events_raw:
                return "You have no upcoming events to cancel."

            # Format events for display and LLM context
            event_list_for_display = []
            event_list_for_llm_context = []
            for e in events_raw:
                title = e.get("summary", "Untitled")
                start = e.get("start", {}).get("dateTime", e.get("start", {}).get("date", ""))
                eid = e.get("id", "") # Event ID is crucial for deletion
                
                display_time = ""
                if start:
                    try:
                        dt = dateparser.parse(start)
                        display_time = dt.strftime("%A, %d %B at %I:%M %p")
                    except:
                        display_time = start # Fallback if parsing fails
                
                event_list_for_display.append(f"• {title} — {display_time}")
                event_list_for_llm_context.append({"id": eid, "title": title, "display": display_time})

            # Handle "cancel all" or similar requests
            msg_lower = user_message.lower()
            if any(w in msg_lower for w in ["all", "every", "all of them", "all meetings", "all events", "clear all"]):
                deleted_count = 0
                deleted_titles = []
                for e in event_list_for_llm_context:
                    try:
                        service.events().delete(calendarId=MAIN_CALENDAR_ID, eventId=e["id"]).execute()
                        deleted_titles.append(e["title"])
                        deleted_count += 1
                    except Exception as e_del:
                        logger.warning(f"Could not delete event {e['id']} ({e['title']}): {e_del}")
                return f"🗑️ Cancelled {deleted_count} upcoming event(s): {', '.join(deleted_titles)}"

            # If not cancelling all, use LLM to pick the specific event
            if not groq:
                return "⚠️ AI is not available to help pick the event. Please specify which event to cancel (e.g., 'cancel meeting with John')."

            event_descriptions_for_llm = "\n".join([f"{i+1}. {e['title']} — {e['display']}" for i, e in enumerate(event_list_for_llm_context)])

            llm_prompt_messages = [
                {
                    "role": "system",
                    "content": f"""You must return ONLY a single digit number corresponding to the event to cancel.
No words, no explanation, no punctuation. Just the number.
If the user's message doesn't clearly match any of the events, return "0".

Today is {datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime('%A, %d %B %Y')}.

Current Events:
{event_descriptions_for_llm}

User ({profile_name}): {user_message}
Recent chat context: {recent_chat}

Example Output: 1 (if user wants to cancel the first event listed)
Example Output: 0 (if unsure or no match)"""
                }
            ]

            llm_response_for_intent = groq.chat.completions.create(
                messages=llm_prompt_messages,
                model="llama-3.1-8b-instant", # Or your preferred lightweight model
                max_tokens=5
            )
            
            choice_str = llm_response_for_intent.choices[0].message.content.strip()
            numbers = re.findall(r'\d+', choice_str)
            
            selected_index = -1
            if numbers:
                idx = int(numbers[0])
                if 1 <= idx <= len(event_list_for_llm_context):
                    selected_index = idx - 1 # Adjust to 0-based index

            if selected_index != -1:
                event_to_cancel = event_list_for_llm_context[selected_index]
                service.events().delete(
                    calendarId=MAIN_CALENDAR_ID,
                    eventId=event_to_cancel["id"]
                ).execute()
                return f"🗑️ *{event_to_cancel['title']}* on {event_to_cancel['display']} has been cancelled."
            else:
                return "I couldn't determine which event you want to cancel. Please be more specific or list the events again."

        except Exception as e:
            logger.error(f"Error in cancel_event: {e}")
            return "⚠️ An error occurred while trying to cancel the event. Please try again."

    # =============================
    # CREATE EVENT — FIXED AND ENHANCED
    # =============================
    def create_and_verify_event(title, dt_str):
        """
        Creates a Google Calendar event, attempts to verify, and corrects if necessary.
        Handles timezone conversions and uses smart parsing.
        """
        service = get_calendar_service()
        if not service:
            return "⚠️ Google Calendar service is unavailable. Please check configuration."

        try:
            # Parse the date and time string robustly
            # dateparser's "prefer dates from future" helps with ambiguous inputs
            dt = dateparser.parse(dt_str, settings={'PREFER_DATES_FROM': 'future'})
            if not dt:
                return "⚠️ I couldn't understand the date and time you provided. Please try again with a clear format like 'tomorrow at 3 PM' or 'May 15th 10:00 AM'."

            # --- Timezone Handling ---
            # Google Calendar API prefers ISO 8601 format.
            # For `dateTime` fields, it expects the offset.
            # We'll parse the input, assume it's intended for IST based on common user locale,
            # and convert it to UTC for the API.
            
            # Define IST timezone offset
            ist_offset_td = timedelta(hours=5, minutes=30)
            ist_timezone = timezone(ist_offset_td)

            # Ensure dt is timezone-aware. If naive, assume it's local time (IST)
            if dt.tzinfo is None:
                dt_aware = dt.replace(tzinfo=ist_timezone)
            else:
                dt_aware = dt # Already timezone-aware

            # Convert the aware datetime object to UTC for Google API
            dt_utc = dt_aware.astimezone(timezone.utc)

            # Calculate end time (defaulting to 1 hour duration)
            # Future enhancements could parse durations like "for 2 hours"
            event_duration = timedelta(hours=1)
            end_dt_utc = dt_utc + event_duration

            # Format for Google Calendar API: ISO 8601 string with timezone offset
            # For dateTime: "2023-10-27T10:00:00-07:00" or "2023-10-27T17:00:00Z" for UTC
            start_iso = dt_utc.isoformat(timespec='seconds') # e.g., '2023-10-27T17:00:00+00:00'
            end_iso = end_dt_utc.isoformat(timespec='seconds')

            # Construct the event body
            event_body = {
                "summary": title,
                "start": {"dateTime": start_iso, "timeZone": "Asia/Kolkata"}, # Use 'timeZone' for human readability and context
                "end": {"dateTime": end_iso, "timeZone": "Asia/Kolkata"},
            }
            
            # --- Event Creation ---
            logger.info(f"Attempting to create event: {title} for {start_iso}")
            created_event = service.events().insert(
                calendarId=MAIN_CALENDAR_ID,
                body=event_body
            ).execute()
            
            event_id = created_event.get("id")
            if not event_id:
                logger.error("Event created but no ID returned.")
                return "⚠️ Event was created, but I couldn't get its details to confirm. Please check your calendar."

            # --- Verification and Correction Step ---
            # Fetch the event that was just created to verify
            verified_event = service.events().get(
                calendarId=MAIN_CALENDAR_ID,
                eventId=event_id
            ).execute()

            saved_title = verified_event.get("summary", "")
            saved_start_time_raw = verified_event.get("start", {}).get("dateTime", "")
            saved_end_time_raw = verified_event.get("end", {}).get("dateTime", "")

            needs_correction = False
            correction_note = ""

            # Check if title matches
            if saved_title != title:
                logger.warning(f"Title mismatch: Expected '{title}', got '{saved_title}'. Correcting.")
                needs_correction = True

            # Check if start time is substantially different (allowing for small API rounding differences)
            if saved_start_time_raw:
                try:
                    saved_dt_utc = dateparser.parse(saved_start_time_raw.replace('Z', '+00:00')) # Parse ISO string
                    if abs((saved_dt_utc - dt_utc).total_seconds()) > 60: # If more than 60 seconds difference
                        logger.warning(f"Start time mismatch: Expected '{dt_utc.isoformat()}', got '{saved_dt_utc.isoformat()}'. Correcting.")
                        needs_correction = True
                except Exception as dt_parse_err:
                    logger.warning(f"Could not parse saved start time '{saved_start_time_raw}' for verification: {dt_parse_err}")
                    needs_correction = True # Treat as a mismatch if parsing fails
            else: # If no start time found after creation, that's a major issue
                logger.error("Saved event has no start time after creation.")
                needs_correction = True

            if needs_correction:
                logger.info(f"Attempting to update event {event_id} due to verification issues.")
                # Re-apply the original event_body to update
                service.events().update(
                    calendarId=MAIN_CALENDAR_ID,
                    eventId=event_id,
                    body=event_body
                ).execute()
                correction_note = " *(auto-corrected ✓)*"
                logger.info(f"Event '{title}' updated successfully.")

            # --- Format for User Display (using IST) ---
            # Convert original UTC datetime back to IST for display
            display_dt_aware_ist = dt_utc.astimezone(ist_timezone)
            display_date_str = display_dt_aware_ist.strftime("%A, %d %B")
            time_range_str = display_dt_aware_ist.strftime("%I:%M %p")
            
            # Handle all-day events if they were somehow created (unlikely with dateTime)
            if 'date' in verified_event.get('start', {}):
                display_dt_all_day = dateparser.parse(verified_event['start']['date'])
                display_date_str = display_dt_all_day.strftime("%A, %d %B")
                time_range_str = "All day"

            return f"📅 *{title}*\n🕐 {display_date_str} at {time_range_str}{correction_note}\n✅ Added to calendar."

        except Exception as e:
            logger.error(f"Error in create_and_verify_event: {e}")
            # Attempt cleanup if an event_id was generated but an error occurred later
            if 'event_id' in locals() and event_id:
                try:
                    logger.warning(f"Attempting to delete partially created event with ID: {event_id}")
                    service.events().delete(calendarId=MAIN_CALENDAR_ID, eventId=event_id).execute()
                    logger.info(f"Successfully cleaned up event ID: {event_id}")
                except Exception as cleanup_e:
                    logger.error(f"Failed to clean up event {event_id}: {cleanup_e}")
            return "⚠️ I encountered an error while trying to add the event. Please check your calendar manually."

except ImportError:
    logger.error("Google Calendar libraries not found. Please install them: pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2 dateparser")
    # Define dummy functions if imports fail
    def get_calendar_service():
        return None
    def get_upcoming_events():
        return []
    def get_events_for_query(user_message):
        return [], "today"
    def cancel_event(user_message, recent_chat, profile_name):
        return "⚠️ Google Calendar functionality is not available due to missing libraries."
    def create_and_verify_event(title, dt_str):
        return "⚠️ Google Calendar functionality is not available due to missing libraries."
except Exception as e:
    logger.error(f"An unexpected error occurred during Google Calendar setup: {e}")
    # Define dummy functions if setup fails
    def get_calendar_service():
        return None
    def get_upcoming_events():
        return []
    def get_events_for_query(user_message):
        return [], "today"
    def cancel_event(user_message, recent_chat, profile_name):
        return "⚠️ Google Calendar functionality is unavailable due to an unexpected error."
    def create_and_verify_event(title, dt_str):
        return "⚠️ Google Calendar functionality is unavailable due to an unexpected error."


# =============================
# DATABASE OPERATIONS (for conversations and profile)
# =============================
def run_query(query, params=(), fetch=False):
    """
    Executes a database query safely. Manages connection lifecycle.
    Returns fetched results if fetch is True, otherwise None.
    Returns empty list for fetches on error.
    """
    conn = None
    try:
        # For Railway, sslmode="require" is often necessary for PostgreSQL
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        result = None
        if fetch:
            result = cursor.fetchall()
        
        conn.commit() # Commit changes for INSERT, UPDATE, DELETE
        return result
    except psycopg2.Error as e:
        logger.error(f"Database error executing query: {query.split(' ')[0]} - {e}")
        if conn:
            conn.rollback() # Rollback on error
        return [] if fetch else None # Return empty list for fetching, None otherwise
    except Exception as e:
        logger.error(f"Unexpected error in run_query: {e}")
        if conn:
            conn.rollback()
        return [] if fetch else None
    finally:
        if conn:
            conn.close()

# =============================
# SUPABASE AI HINTS
# =============================
def get_query_hints(user_message):
    """Fetches contextual hints from Supabase AI endpoint."""
    if not SUPABASE_ANON_KEY or not SUPABASE_FUNCTION_URL:
        logger.warning("Supabase keys/URL not set. Cannot fetch query hints.")
        return []
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
        }
        response = requests.post(
            SUPABASE_FUNCTION_URL,
            headers=headers,
            json={"question": user_message},
            timeout=5 # Set a timeout for the request
        )
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        return response.json().get("hints", [])
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Supabase AI endpoint: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error processing Supabase AI response: {e}")
        return []

# =============================
# CONVERSATION MEMORY MANAGEMENT
# =============================
def get_recent_chat(uid, user_message):
    """Retrieves recent chat history for context, focusing on relevant parts."""
    try:
        r = run_query(
            "SELECT recent_chat FROM conversations WHERE user_id=%s",
            (uid,), True
        )
        if not r or not r[0] or not r[0][0]: # If no history found or it's empty
            return ""

        history_str = r[0][0]
        lines = history_str.split("\n")

        # Heuristic: If user message contains reference words, look further back.
        # Otherwise, take the most recent messages.
        ref_words = ["that", "it", "this", "before", "earlier", "you said", "mentioned"]
        if any(w in user_message.lower() for w in ref_words):
            # Take last 14 messages (approx 7 turns) and prepend the user's current message as context
            relevant_history = "\n".join(lines[-14:])
        else:
            # Take last 8 messages (approx 4 turns)
            relevant_history = "\n".join(lines[-8:])
        
        return relevant_history
        
    except Exception as e:
        logger.error(f"Error retrieving recent chat history for {uid}: {e}")
        return ""

def update_recent_chat(uid, user_message, jarvis_response_text):
    """Appends the latest user message and Jarvis's response to the conversation log."""
    # Format the new entries clearly
    new_log_entry = f"User: {user_message}\nJarvis: {jarvis_response_text}"
    
    try:
        # Fetch existing history first to append to it
        existing_chat_result = run_query("SELECT recent_chat FROM conversations WHERE user_id=%s", (uid,), fetch=True)
        existing_chat = ""
        if existing_chat_result and existing_chat_result[0] and existing_chat_result[0][0]:
            existing_chat = existing_chat_result[0][0]
        
        # Combine and prune to avoid excessive length (e.g., keep last N characters or lines)
        combined_chat = (existing_chat + "\n" + new_log_entry).strip()
        
        # Simple pruning: Keep last ~2000 characters or ~50 lines to manage DB size
        lines = combined_chat.split('\n')
        if len(lines) > 50:
            combined_chat = "\n".join(lines[-50:])
        
        run_query("""
            INSERT INTO conversations (user_id, recent_chat)
            VALUES (%s, %s)
            ON CONFLICT(user_id)
            DO UPDATE SET recent_chat = conversations.recent_chat || %s;
        """, (uid, new_log_entry, "\n" + new_log_entry)) # Append new entry to existing
        logger.info(f"Updated conversation history for user {uid}.")
    except Exception as e:
        logger.error(f"Error updating recent chat history for {uid}: {e}")

# =============================
# PROFILE MANAGEMENT
# =============================
def load_profile(uid):
    """Loads user profile data from the database."""
    try:
        query = f"SELECT {', '.join(PROFILE_COLUMNS)} FROM profile WHERE user_id=%s;"
        r = run_query(query, (uid,), fetch=True)
        
        if not r:
            return {} # Return empty dict if no profile exists

        profile_data = {}
        # Get column names for the current query to map results to keys
        # This assumes the query selects columns in the order of PROFILE_COLUMNS
        # A more robust way: use `cursor.description` if you have access to cursor
        for i, col_name in enumerate(PROFILE_COLUMNS):
            # Ensure index is within bounds of the returned row
            if i < len(r[0]) and r[0][i] is not None:
                profile_data[col_name] = r[0][i]
        return profile_data
    except Exception as e:
        logger.error(f"Error loading profile for user {uid}: {e}")
        return {}

def format_profile_for_llm(profile):
    """Formats profile for LLM prompt, including only non-empty fields."""
    if not profile:
        return "No profile data available."
    
    lines = []
    for k in PROFILE_COLUMNS: # Iterate in defined order
        v = profile.get(k)
        if v and v.strip(): # Only include if value exists and is not empty
            lines.append(f"{k.replace('_', ' ').title()}: {v}")

    return "\n".join(lines) if lines else "No profile data available."

def extract_and_save_facts(uid, user_message, jarvis_reply, current_profile):
    """
    Uses LLM to extract explicit facts from user message and Jarvis's reply about the user.
    Saves these facts to the profile table.
    """
    if not groq:
        logger.warning("Groq client not available, cannot extract facts.")
        return

    profile_summary_for_llm = format_profile_for_llm(current_profile)
    all_columns_str = ", ".join(PROFILE_COLUMNS)

    try:
        llm_response_raw = groq.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"""You are a meticulous fact extractor. Your sole purpose is to identify EXPLICIT facts stated by the USER in their message and the AI's reply, related to the user's PROFILE.

Current User Profile (for context, DO NOT invent or change):
{profile_summary_for_llm}

Available profile fields you can update (use exact field names):
{all_columns_str}

ABSOLUTE RULES:
1.  **EXPLICIT FACTS ONLY:** Extract information ONLY if the USER has stated it directly and clearly. Never infer, assume, guess, or extrapolate.
2.  **NO QUESTIONS:** Ignore any information contained in questions or hypotheticals.
3.  **USER-SOURCED:** Only facts stated by the USER are saved. Do NOT save anything Jarvis said, UNLESS it's a direct confirmation of something the USER just *explicitly* stated AND Jarvis is confirming it back to the user.
4.  **NO CALENDAR/EVENTS:** Do NOT extract anything related to calendar events, meetings, reminders, appointments, or schedules. These are temporary and not profile facts.
5.  **NO HALLUCINATIONS:** If the user implies something or if Jarvis says something that *might* be true but isn't explicitly stated by the user, DO NOT SAVE IT.
6.  **FIELD MATCHING:** Use the exact field names provided. If the user says "I'm studying Physics", and "Physics" can map to "subjects", save it. If it's unclear, do not save. For generic praise like "I'm good at coding", if "technical_skills" is a field, you can map it.
7.  **TRIVIAL INFORMATION:** Do not save common filler words or contextless statements. E.g., "yes", "no", "okay", "stop it".
8.  **NEW VS. UPDATE:** If a field already exists in the profile, and the user states a new value for it, update it. If the user states a value for a new field, add it.
9.  **FORMAT:** Respond with key-value pairs separated by a colon, one per line. If no new facts are extracted, respond with EXACTLY "NONE".

Examples of what to extract:
- User: "My name is John." → name: John
- User: "I live in London." → location: London
- User: "I'm in 10th grade." → grade: 10th
- User: "I want to be a doctor." → dream_job: doctor
- User: "I'm working on a project called 'AI Assistant'." → active_projects: AI Assistant
- User said: "My favorite subject is Math." Jarvis said: "Okay, Math is your favorite subject." → favourite_subject: Math

Examples of what NOT to extract:
- User: "Do you remember my favorite color?" Jarvis: "I don't have that information." → NONE
- User: "I need to schedule a meeting." → NONE (Calendar event)
- User: "Stop saying I have exams." → NONE (Implied, not explicit profile fact)
- User: "I want to learn coding." → learning_style: coding (if 'learning_style' is a suitable field) OR technical_skills: coding
- User: "My friend Alex is coming over." → friends: Alex (if "friends" is a field)
- User: "I'm feeling tired." → No direct profile field for 'feeling tired'. Could be 'energy_patterns' if context fits strictly. Usually NONE.

Your output MUST be plain text, one fact per line. If no facts, output ONLY 'NONE'."""
                },
                {
                    "role": "user",
                    "content": f"User's message: {user_message}\nJarvis's reply: {jarvis_reply}\n\nPrevious profile summary:\n{profile_summary_for_llm}"
                }
            ],
            model="llama-3.1-8b-instant", # Use a lightweight, fast model for fact extraction
            max_tokens=300
        )

        extracted_text = llm_response_raw.choices[0].message.content.strip()
        logger.info(f"Raw fact extraction output: {extracted_text}")

        if extracted_text.upper().startswith("NONE"):
            logger.info("No new explicit facts extracted.")
            return

        updates = {}
        for line in extracted_text.split("\n"):
            line = line.strip()
            if ":" in line:
                parts = line.split(":", 1)
                field_raw = parts[0].strip().lower()
                value = parts[1].strip()

                # Normalize field names to match PROFILE_COLUMNS (e.g., "Favorite Subject" -> "favourite_subject")
                normalized_field = field_raw.replace(" ", "_").replace("-", "_")
                
                # Check if the normalized field exists in our PROFILE_COLUMNS
                if normalized_field in PROFILE_COLUMNS and value:
                    updates[normalized_field] = value
                else:
                    logger.warning(f"Extracted field '{field_raw}' (normalized: '{normalized_field}') not in PROFILE_COLUMNS or value is empty. Skipping.")

        if not updates:
            logger.info("No valid facts parsed from extraction output.")
            return

        # Prepare the SQL query for updating or inserting profile data
        # This uses INSERT ... ON CONFLICT to atomically insert or update
        set_clause = ", ".join([f"{k} = EXCLUDED.{k}" for k in updates.keys()]) # For the DO UPDATE part
        column_names = ["user_id"] + list(updates.keys())
        placeholders = ", ".join(["%s"] * (len(updates) + 1)) # For VALUES part
        values = [uid] + list(updates.values()) # For VALUES part

        query = f"""
            INSERT INTO profile ({", ".join(column_names)})
            VALUES ({placeholders})
            ON CONFLICT(user_id)
            DO UPDATE SET {set_clause};
        """

        run_query(query, values)
        logger.info(f"Profile updated for user {uid} with facts: {updates}")

    except Exception as e:
        logger.error(f"Error during fact extraction and saving for user {uid}: {e}")

# =============================
# INTENT CLASSIFICATION
# =============================
def classify_intent(user_message, recent_chat, profile_name="user"):
    """Classifies user's intent using LLM."""
    if not groq:
        logger.warning("Groq client not available. Defaulting intent to CHAT.")
        return "CHAT"

    try:
        llm_prompt_messages = [
            {
                "role": "system",
                "content": """You are an intent classifier for an AI assistant named Jarvis.
Your task is to analyze the user's input and categorize their primary intent.
Respond ONLY with a single, uppercase label.

Available Intents:
-   **GREETING**: Informal greetings ('hello', 'hi', 'hey', 'halo', 'sup', 'yo').
-   **QUESTION**: Asking for factual information, explanations, advice, or definitions. Usually involves 'what is', 'how does', 'why does', 'explain'.
-   **ADD_EVENT**: User wants to CREATE or SCHEDULE a new event, meeting, reminder, or appointment. Keywords: 'add', 'schedule', 'set', 'create', 'book', 'remind me', 'meeting', 'event'.
-   **CANCEL_EVENT**: User wants to DELETE or CANCEL an existing event or meeting. Keywords: 'cancel', 'delete', 'remove', 'don't want'.
-   **RECALL**: User is asking ABOUT their existing schedule, past information, saved profile data, or prior AI responses. Often involves questions about 'my calendar', 'my events', 'what did I ask', 'what did you say'.
-   **CHAT**: General conversation, small talk, affirmations, reactions, or statements that don't clearly fit other intents. This is the default if no other intent is strong.

CRITICAL RULES:
1.  **Specificity:** If the user's message strongly suggests 'ADD_EVENT', 'CANCEL_EVENT', 'RECALL', or 'QUESTION', assign that specific intent.
2.  **Default to CHAT:** If the intent is ambiguous or nonsensical, default to 'CHAT'.
3.  **Context Matters:** Consider the `recent_chat` for context, especially for 'RECALL' vs. 'QUESTION'.
4.  **No Calendar Events in Questions:** A question like "what meetings do I have tomorrow?" should be 'RECALL', not 'QUESTION'.
5.  **Calendar Creation vs. Recall:** "schedule meeting tomorrow at 3pm" is 'ADD_EVENT'. "Do I have a meeting tomorrow?" is 'RECALL'.
6.  **Output Format:** Respond ONLY with the label, e.g., `ADD_EVENT`. No extra text.

Examples:
- "halo" → GREETING
- "what is the capital of France?" → QUESTION
- "schedule a meeting for Friday at 9 AM" → ADD_EVENT
- "tomorrow at 5pm add 'Doctor Appointment'" → ADD_EVENT
- "cancel my 3 PM meeting" → CANCEL_EVENT
- "delete all my events for today" → CANCEL_EVENT
- "what's on my agenda today?" → RECALL
- "did I ask about Python yesterday?" → RECALL
- "sounds good" → CHAT
- "I'm feeling tired" → CHAT
"""
            },
            {
                "role": "user",
                "content": f"User message: {user_message}\nRecent chat:\n{recent_chat}"
            }
        ]

        response = groq.chat.completions.create(
            messages=llm_prompt_messages,
            model="llama-3.1-8b-instant", # Use a fast, lightweight model
            max_tokens=15 # Expecting a short label
        )
        
        intent = response.choices[0].message.content.strip().upper()
        
        # Simple validation to ensure it's one of the expected intents
        valid_intents = ["GREETING", "QUESTION", "ADD_EVENT", "CANCEL_EVENT", "RECALL", "CHAT"]
        if intent in valid_intents:
            logger.info(f"Classified intent: {intent} for message: '{user_message}'")
            return intent
        else:
            logger.warning(f"Unrecognized intent '{intent}' received from LLM. Defaulting to CHAT. Message: '{user_message}'")
            return "CHAT" # Fallback

    except Exception as e:
        logger.error(f"Error classifying intent for message '{user_message}': {e}. Defaulting to CHAT.")
        return "CHAT"

# =============================
# EVENT EXTRACTION HELPER
# =============================
def extract_event_details(user_message, recent_chat, profile):
    """
    Uses LLM to extract a smart title and a full datetime string for an event.
    """
    if not groq:
        logger.warning("Groq client not available. Cannot extract event details.")
        return None

    # Get current time in IST for LLM context
    try:
        ist_tz = timezone(timedelta(hours=5, minutes=30))
        current_dt_ist_naive = datetime.now(ist_tz).replace(tzinfo=None) # Naive datetime for dateparser
        current_dt_str_display = current_dt_ist_naive.strftime("%A, %d %B %Y, %I:%M %p")
    except Exception as tz_err:
        logger.error(f"Could not determine IST timezone for event extraction context: {tz_err}. Using UTC.")
        current_dt_ist_naive = datetime.utcnow().replace(tzinfo=None)
        current_dt_str_display = current_dt_ist_naive.strftime("%A, %d %B %Y, %I:%M %p UTC") # Indicate UTC

    profile_name = profile.get("name", "user")
    active_projects = profile.get("active_projects", "no known active projects")

    try:
        llm_response_raw = groq.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"""You are an AI assistant for extracting event details. Your goal is to identify a SMART TITLE and a COMPLETE DATETIME for a potential event.

CURRENT DATE & TIME (for context): {current_dt_str_display}

USER CONTEXT:
- Name: {profile_name}
- Active Projects: {active_projects}

INSTRUCTIONS:
1.  **SMART TITLE:**
    -   Generate a descriptive event title based on the user's message and context.
    -   NEVER include time, date, or words like "today", "tomorrow" in the title.
    -   If the purpose is unclear, use a generic title like "Meeting" or "Event".
    -   If there's context (e.g., "project meeting", "doctor's appointment"), use that.
    -   Examples: "School Project Meetup", "Doctor Appointment", "Catch up with John".
2.  **COMPLETE DATETIME:**
    -   Extract the FULL date and time mentioned.
    -   If no time is specified, assume 12:00 PM (noon).
    -   If no date is specified, assume TODAY's date (using the provided CURRENT DATE & TIME as reference).
    -   Provide the datetime in a clear format that `dateparser.parse()` can understand, e.g., "23 March 2026 at 4:00 PM".
    -   Handle relative terms like "tomorrow", "next week", "Friday evening".
3.  **OUTPUT FORMAT:** Respond EXACTLY in the following format:
    TITLE: <Your smart title>
    DATETIME: <Full datetime string like "23 March 2026 at 4:00 PM">
    If you cannot extract a title or datetime, return "TITLE: NOT_SPECIFIED\nDATETIME: NOT_SPECIFIED".

CRITICAL RULES:
-   Do NOT extract information from the `Recent chat` EXCEPT to resolve ambiguity or provide context for the title/datetime. The main message should be the focus.
-   NEVER invent information. If a detail is truly missing, use "NOT_SPECIFIED" for that part.
-   Be concise and precise.
"""
                },
                {
                    "role": "user",
                    "content": f"User's latest message: {user_message}\nRecent chat context:\n{recent_chat}"
                }
            ],
            model="llama-3.1-8b-instant", # Use a fast model that excels at structured extraction
            max_tokens=200
        )

        output_text = llm_response_raw.choices[0].message.content.strip()
        
        title = "NOT_SPECIFIED"
        dt_str = "NOT_SPECIFIED"

        for line in output_text.split("\n"):
            line = line.strip()
            if line.startswith("TITLE:"):
                title = line.replace("TITLE:", "").strip()
            elif line.startswith("DATETIME:"):
                dt_str = line.replace("DATETIME:", "").strip()

        if title == "NOT_SPECIFIED" or dt_str == "NOT_SPECIFIED":
            logger.warning(f"Could not extract full event details from message: '{user_message}'. Output was: {output_text}")
            return None # Indicate failure to extract

        logger.info(f"Extracted event: Title='{title}', Datetime='{dt_str}'")
        return {"title": title, "datetime": dt_str}

    except Exception as e:
        logger.error(f"Error during event detail extraction for message '{user_message}': {e}")
        return None

# =============================
# RECALL HANDLER
# =============================
def handle_recall(user_message, recent_chat, hints, profile):
    """Handles 'RECALL' intent by fetching calendar events and using LLM to answer."""
    events_formatted, time_label = get_events_for_query(user_message)
    events_text = "\n".join(events_formatted) if events_formatted else f"No events found for {time_label}."

    profile_name = profile.get("name", "user")

    if not groq:
        logger.warning("Groq client not available. Returning raw event data for recall.")
        return f"Regarding {time_label}: {events_text}"

    try:
        llm_prompt_messages = [
            {
                "role": "system",
                "content": f"""You are Jarvis. Your purpose is to answer the user's specific question using ONLY the provided calendar and profile information.

YOUR STRICT RULES:
1.  **USE PROVIDED DATA ONLY:** Base your response SOLELY on the 'Calendar Events' and 'User Profile' data. Do NOT invent or infer anything outside of this.
2.  **ANSWER SPECIFICALLY:** Address the user's question directly. If they ask 'what's on my schedule tomorrow?', answer THAT. Do not volunteer extra information.
3.  **NO CALENDAR MANAGEMENT:** Do NOT perform actions like adding or cancelling events here. This is for answering questions ONLY.
4.  **BE CONCISE:** Responses should be short, typically 1-3 sentences.
5.  **HANDLE NO DATA:** If no relevant calendar events are found for the requested period, state that clearly.
6.  **USE PROFILE DATA:** Naturally incorporate the user's name from the profile if appropriate.
7.  **STYLE:** Maintain Jarvis's personality (calm, intelligent, direct).

Examples:
- User asks "When is my doctor's appointment?" and data shows "• Doctor Appointment — Tuesday, 20 February at 09:00 AM". Your response: "Your doctor's appointment is on Tuesday, 20 February at 9:00 AM."
- User asks "What's happening today?" and no events for today. Your response: "You have no events scheduled for today."
- User asks "What should I do?" and profile mentions "long_term_goals: Travel the world". Your response: "Considering your long-term goal to travel the world, perhaps you could plan your next adventure." (Only if directly relevant and concise)
"""
            },
            {
                "role": "user",
                "content": f"""User's question: {user_message}

Calendar Events for {time_label}:
{events_text}

User Profile:
Name: {profile_name}
(other relevant profile context if needed, but keep it brief here for recall)

Recent chat context:
{recent_chat}"""
            }
        ]

        response = groq.chat.completions.create(
            messages=llm_prompt_messages,
            model="llama-3.1-8b-instant",
            max_tokens=150
        )
        
        answer = response.choices[0].message.content.strip()
        
        # Fallback if LLM fails to provide a good answer
        if not answer or answer.startswith("I cannot") or answer.startswith("I don't have"):
            return f"Regarding {time_label}: {events_text}"
        
        return answer

    except Exception as e:
        logger.error(f"Error in handle_recall for message '{user_message}': {e}. Returning raw event data.")
        return f"Regarding {time_label}: {events_text}"

# =============================
# GENERAL AI RESPONSE (when no specific intent is matched)
# =============================
def ask_jarvis_generally(user_message, recent_chat, hints, profile):
    """Generates a general response using LLM based on profile and personality."""
    if not groq:
        logger.warning("Groq client not available. Returning generic fallback.")
        return "I'm having trouble connecting to my intelligence module right now. How can I help?"

    try:
        profile_text_for_llm = format_profile_for_llm(profile)

        llm_prompt_messages = [
            {
                "role": "system",
                "content": PERSONALITY # Apply Jarvis's personality rules
            },
            {
                "role": "user",
                "content": f"""User's message: {user_message}

User's Profile (for context):
{profile_text_for_llm}

Recent conversation context:
{recent_chat}

Contextual hints from AI:
{", ".join(hints) if hints else "N/A"}

Your task is to respond conversationally and concisely, embodying Jarvis.
Avoid mentioning calendar events or schedules unless the user explicitly asks about them.
Be smart, direct, and slightly witty if appropriate, but never robotic or overly friendly.
Keep your response short (1-3 sentences)."""
            }
        ]

        response = groq.chat.completions.create(
            messages=llm_prompt_messages,
            model="llama-3.1-8b-instant",
            max_tokens=150
        )
        
        answer = response.choices[0].message.content.strip()
        
        # Basic fallback if LLM returns something unhelpful
        if not answer or len(answer) < 5:
            return "Is there something specific I can help you with?"
        
        return answer

    except Exception as e:
        logger.error(f"Error in ask_jarvis_generally for message '{user_message}': {e}")
        return "I'm sorry, I'm experiencing a temporary issue. Please try again later."

# =============================
# TWILIO WHATSAPP WEBHOOK
# =============================
@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    """Handles incoming WhatsApp messages, processes them, and sends replies."""
    try:
        # Get data from Twilio request
        form_data = request.form
        uid = form_data.get("From") # Sender's phone number (unique identifier)
        incoming_msg = form_data.get("Body", "").strip()

        if not uid:
            logger.warning("Received webhook request without 'From' number. Ignoring.")
            return "OK" # Acknowledge receipt but do nothing

        logger.info(f"Received message from {uid}: '{incoming_msg}'")

        # --- Load Context ---
        # Fetch recent chat history for context
        recent_chat_context = get_recent_chat(uid, incoming_msg)
        # Fetch hints from Supabase if available
        query_hints = get_query_hints(incoming_msg)
        # Load user profile data
        user_profile = load_profile(uid)
        profile_name = user_profile.get("name", "user") # Get name for persona use

        # --- Pre-processing: Extract facts before main intent analysis ---
        # This helps enrich profile data immediately upon user input if a fact is stated
        extract_and_save_facts(uid, incoming_msg, "", user_profile)
        # Reload profile in case facts were updated
        user_profile = load_profile(uid) 

        # --- Intent Classification ---
        user_intent = classify_intent(incoming_msg, recent_chat_context, profile_name)
        logger.info(f"Intent classified as: {user_intent}")

        # --- Route based on Intent ---
        jarvis_response_text = ""

        if user_intent == "ADD_EVENT":
            event_details = extract_event_details(incoming_msg, recent_chat_context, user_profile)
            if event_details and event_details.get("title") != "NOT_SPECIFIED" and event_details.get("datetime") != "NOT_SPECIFIED":
                jarvis_response_text = create_and_verify_event(event_details["title"], event_details["datetime"])
            else:
                jarvis_response_text = "I couldn't quite figure out the event details. Could you please provide the title and a clear date/time?"
        
        elif user_intent == "CANCEL_EVENT":
            jarvis_response_text = cancel_event(incoming_msg, recent_chat_context, profile_name)
        
        elif user_intent == "RECALL":
            jarvis_response_text = handle_recall(incoming_msg, recent_chat_context, query_hints, user_profile)
        
        elif user_intent == "GREETING":
            # If it's just a greeting, respond with a conversational greeting
            # Use the generic ask function with a prompt focused on greetings
            greeting_message = "Just a simple hello to see if you're there."
            jarvis_response_text = ask_jarvis_generally(greeting_message, recent_chat_context, query_hints, user_profile)
            if not jarvis_response_text or len(jarvis_response_text) < 5: # Basic fallback
                jarvis_response_text = f"Hello {profile_name}! How can I help you today?"

        elif user_intent == "QUESTION":
            # For direct questions, use the general AI response handler
            jarvis_response_text = ask_jarvis_generally(incoming_msg, recent_chat_context, query_hints, user_profile)
        
        elif user_intent == "CHAT":
            # For general chat, use the general AI response handler
            jarvis_response_text = ask_jarvis_generally(incoming_msg, recent_chat_context, query_hints, user_profile)

        else: # Fallback if intent is unknown or not handled
            logger.warning(f"Unrecognized or unhandled intent '{user_intent}' for message '{incoming_msg}'. Falling back to general chat.")
            jarvis_response_text = ask_jarvis_generally(incoming_msg, recent_chat_context, query_hints, user_profile)

        # --- Post-processing: Update memory and extract facts from entire exchange ---
        # This saves the latest interaction and allows profile to be updated from what Jarvis said (if it confirms user input)
        update_recent_chat(uid, incoming_msg, jarvis_response_text)
        extract_and_save_facts(uid, incoming_msg, jarvis_response_text, user_profile) # Reload profile if needed

        # --- Send Response ---
        response = MessagingResponse()
        message_obj = response.message(jarvis_response_text)
        
        # Optional: Add media, links, etc. based on response content here if needed
        
        return str(response)

    except Exception as e:
        # Catch-all for any unhandled errors during webhook processing
        logger.critical(f"Unhandled exception in whatsapp_webhook for UID {uid}: {e}", exc_info=True)
        response = MessagingResponse()
        response.message("I'm experiencing a critical issue and cannot process your request right now. Please try again later.")
        return str(response)

# =============================
# MAIN APPLICATION RUN BLOCK
# =============================
if __name__ == "__main__":
    # When running on platforms like Railway, PORT is provided by the environment.
    # Locally, it defaults to 8080.
    PORT = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting Flask application on port {PORT}")
    
  
```
