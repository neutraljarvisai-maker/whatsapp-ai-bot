import os
import logging
from flask import Flask, request, jsonify
from core.brain import brain
from services.profile_util import load_profile, format_profile_for_llm
from core.personality import PERSONALITY, PROFILE_COLUMNS
from services.database import run_query
from services.calendar_util import get_calendar_service, get_events_for_query, create_and_verify_event, cancel_event
from twilio.twiml.messaging_response import MessagingResponse
import uuid

# Initialize Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- ENDPOINTS ---

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "bat-jarvis-desktop-backend"})

@app.route("/chat", methods=["POST"])
def chat():
    """General chat endpoint for the desktop client using single-call architecture."""
    data = request.json
    uid = data.get("user_id")
    message = data.get("message")

    if not uid or not message:
        return jsonify({"error": "Missing user_id or message"}), 400

    profile = load_profile(uid)
    profile_text = format_profile_for_llm(profile)

    # History retrieval
    history_rows = run_query("SELECT recent_chat FROM conversations WHERE user_id=%s", (uid,), fetch=True)
    history_text = history_rows[0][0] if history_rows else ""

    # Unified Processing
    context = f"Profile Context:\n{profile_text}\n\nRecent History:\n{history_text}"
    result = brain.process_user_message(PERSONALITY, message, context)

    intent = result.get("intent", "CHAT")
    response = result.get("response", "Processing...")

    # Handle Task Intent immediately for client
    if intent == "TASK":
        return jsonify({
            "response": response,
            "intent": "TASK",
            "task": message
        })

    # Handle Facts and Events in background
    facts = result.get("facts", {})
    if facts:
        for field, value in facts.items():
            if field in PROFILE_COLUMNS:
                run_query(f"UPDATE profile SET {field} = %s WHERE user_id = %s", (value, uid))

    event = result.get("event", {})
    if intent == "ADD_EVENT" and event:
        create_and_verify_event(event.get("title", "Event"), event.get("datetime", ""))

    # Update history
    new_entry = f"User: {message}\nVECTA: {response}"
    run_query("""
        INSERT INTO conversations (user_id, recent_chat)
        VALUES (%s, %s)
        ON CONFLICT(user_id)
        DO UPDATE SET recent_chat = conversations.recent_chat || '\n' || %s;
    """, (uid, new_entry, new_entry))

    return jsonify({
        "response": response,
        "intent": intent
    })

@app.route("/plan_action", methods=["POST"])
def plan_action():
    """Vision-based endpoint to plan the next desktop action."""
    if 'screenshot' not in request.files:
        return jsonify({"error": "No screenshot uploaded"}), 400

    screenshot = request.files['screenshot']
    task = request.form.get("task")
    uid = request.form.get("user_id")
    history = request.form.get("history", "").split("|") # Pipe-separated history

    if not task or not uid:
        return jsonify({"error": "Missing task or user_id"}), 400

    # Save screenshot temporarily
    temp_path = f"/tmp/{uuid.uuid4()}.png"
    screenshot.save(temp_path)

    try:
        action = brain.analyze_screen_and_plan(temp_path, task, history)
        return jsonify({"action": action})
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    """Handles incoming WhatsApp messages using single-call architecture."""
    try:
        form_data = request.form
        uid = form_data.get("From")
        incoming_msg = form_data.get("Body", "").strip()

        if not uid: return "OK"

        logger.info(f"WhatsApp msg from {uid}: {incoming_msg}")

        # Load context
        profile = load_profile(uid)
        profile_text = format_profile_for_llm(profile)

        # History retrieval
        history_rows = run_query("SELECT recent_chat FROM conversations WHERE user_id=%s", (uid,), fetch=True)
        history_text = history_rows[0][0] if history_rows else ""

        # Unified Processing
        context = f"Profile Context:\n{profile_text}\n\nRecent History:\n{history_text}"
        result = brain.process_user_message(PERSONALITY, incoming_msg, context)

        intent = result.get("intent", "CHAT")
        response_text = result.get("response", "I'm listening.")

        # Handle Calendar Recall specifically for text response
        if intent == "RECALL":
            events, label = get_events_for_query(incoming_msg)
            events_text = "\n".join(events) if events else f"No events found for {label}."
            # We already have a response from Gemini, but for recall we might want to enrich it
            # To stay within 1 call, Gemini should ideally have been told about the calendar.
            # For now, let's append events if it was a recall.
            if events: response_text += f"\n\nSchedule for {label}:\n{events_text}"

        # Handle Facts and Events
        facts = result.get("facts", {})
        if facts:
            for field, value in facts.items():
                if field in PROFILE_COLUMNS:
                    run_query(f"UPDATE profile SET {field} = %s WHERE user_id = %s", (value, uid))

        event = result.get("event", {})
        if intent == "ADD_EVENT" and event:
            response_text = create_and_verify_event(event.get("title", "Event"), event.get("datetime", ""))

        # Update history
        new_entry = f"User: {incoming_msg}\nVECTA: {response_text}"
        run_query("""
            INSERT INTO conversations (user_id, recent_chat)
            VALUES (%s, %s)
            ON CONFLICT(user_id)
            DO UPDATE SET recent_chat = conversations.recent_chat || '\n' || %s;
        """, (uid, new_entry, new_entry))

        twiml_resp = MessagingResponse()
        twiml_resp.message(response_text)
        return str(twiml_resp)

    except Exception as e:
        logger.error(f"WhatsApp error: {e}")
        return "Error"

@app.route("/update_profile_manual", methods=["POST"])
def update_profile_manual():
    """Endpoint to manually trigger a profile fact update from text."""
    data = request.json
    uid = data.get("user_id")
    message = data.get("message")

    if not uid or not message:
        return jsonify({"error": "Missing parameters"}), 400

    profile = load_profile(uid)
    profile_text = format_profile_for_llm(profile)

    # Use unified method for extraction
    result = brain.process_user_message("Extract profile facts from the message.", message, profile_text)
    facts = result.get("facts", {})

    if facts:
        for field, value in facts.items():
            if field in PROFILE_COLUMNS:
                run_query(f"UPDATE profile SET {field} = %s WHERE user_id = %s", (value, uid))
        return jsonify({"status": "updated", "facts": facts})

    return jsonify({"status": "no_new_facts"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
