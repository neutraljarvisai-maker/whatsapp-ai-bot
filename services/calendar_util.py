import os
import json
import logging
from datetime import datetime, timedelta, timezone
import dateparser
from google.oauth2 import service_account
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

GOOGLE_SERVICE_JSON = os.environ.get("GOOGLE_SERVICE_JSON")
MAIN_CALENDAR_ID = os.environ.get("MAIN_CALENDAR_ID", "primary")
SCOPES = ["https://www.googleapis.com/auth/calendar"]

def get_calendar_service():
    if not GOOGLE_SERVICE_JSON:
        logger.error("GOOGLE_SERVICE_JSON not set.")
        return None
    try:
        service_account_info = json.loads(GOOGLE_SERVICE_JSON)
        creds = service_account.Credentials.from_service_account_info(
            service_account_info, scopes=SCOPES
        )
        return build("calendar", "v3", credentials=creds)
    except Exception as e:
        logger.error(f"Calendar init error: {e}")
        return None

def get_events_in_range(service, time_min, time_max):
    try:
        result = service.events().list(
            calendarId=MAIN_CALENDAR_ID,
            timeMin=time_min.isoformat() + "Z",
            timeMax=time_max.isoformat() + "Z",
            maxResults=10,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        return result.get("items", [])
    except Exception as e:
        logger.error(f"Error fetching events: {e}")
        return []

def format_event(e):
    title = e.get("summary", "Untitled")
    start = e.get("start", {}).get("dateTime", e.get("start", {}).get("date", ""))
    if not start: return f"• {title}"
    if "T" in start:
        dt = dateparser.parse(start)
        display = dt.strftime("%A, %d %B at %I:%M %p")
    else:
        dt = dateparser.parse(start)
        display = dt.strftime("%A, %d %B")
    return f"• {title} — {display}"

def get_events_for_query(user_message):
    service = get_calendar_service()
    if not service: return [], "today"

    now = datetime.now(timezone.utc)
    # Default to today
    start_dt = now.replace(hour=0, minute=0, second=0)
    end_dt = now.replace(hour=23, minute=59, second=59)
    label = "today"

    msg_lower = user_message.lower()
    if "tomorrow" in msg_lower:
        start_dt += timedelta(days=1)
        end_dt += timedelta(days=1)
        label = "tomorrow"

    events = get_events_in_range(service, start_dt, end_dt)
    return [format_event(e) for e in events], label

def create_and_verify_event(title, dt_str):
    service = get_calendar_service()
    if not service: return "Calendar service unavailable."

    dt = dateparser.parse(dt_str)
    if not dt: return "Couldn't parse date."

    start_iso = dt.isoformat()
    end_iso = (dt + timedelta(hours=1)).isoformat()

    event = {
        "summary": title,
        "start": {"dateTime": start_iso, "timeZone": "UTC"},
        "end": {"dateTime": end_iso, "timeZone": "UTC"},
    }

    try:
        created = service.events().insert(calendarId=MAIN_CALENDAR_ID, body=event).execute()
        return f"Event '{title}' created successfully."
    except Exception as e:
        return f"Error creating event: {e}"

def cancel_event(user_message, context):
    # Simplified cancel for now
    return "Event cancellation is not yet fully implemented in the new core."
