import os
import logging
from flask import Flask, request, jsonify
from core.brain import brain
from core.profile_util import load_profile, format_profile_for_llm
from core.personality import PERSONALITY, PROFILE_COLUMNS
from core.database import run_query
from core.calendar_util import get_calendar_service, get_events_for_query, create_and_verify_event, cancel_event
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
    """General chat endpoint for the desktop client."""
    data = request.json
    uid = data.get("user_id")
    message = data.get("message")

    if not uid or not message:
        return jsonify({"error": "Missing user_id or message"}), 400

    profile = load_profile(uid)
    profile_text = format_profile_for_llm(profile)

    # Simple history retrieval (can be expanded)
    history_rows = run_query("SELECT recent_chat FROM conversations WHERE user_id=%s", (uid,), fetch=True)
    history_text = history_rows[0][0] if history_rows else ""

    # First, classify intent to see if it's a TASK
    intent = brain.classify_intent(message, history_text)

    if intent == "TASK":
        return jsonify({
            "response": "Understood. I'm taking control now.",
            "intent": "TASK",
            "task": message
        })

    response = brain.generate_response(
        system_instruction=PERSONALITY,
        user_prompt=f"Profile Context:\n{profile_text}\n\nRecent History:\n{history_text}\n\nUser Message: {message}"
    )

    # Update history
    new_entry = f"User: {message}\nJarvis: {response}"
    run_query("""
        INSERT INTO conversations (user_id, recent_chat)
        VALUES (%s, %s)
        ON CONFLICT(user_id)
        DO UPDATE SET recent_chat = conversations.recent_chat || '\n' || %s;
    """, (uid, new_entry, new_entry))

    return jsonify({"response": response})

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
    """Handles incoming WhatsApp messages."""
    try:
        form_data = request.form
        uid = form_data.get("From")
        incoming_msg = form_data.get("Body", "").strip()

        if not uid: return "OK"

        logger.info(f"WhatsApp msg from {uid}: {incoming_msg}")

        # Load context
        profile = load_profile(uid)
        profile_name = profile.get("name", "user")

        # Simple history retrieval
        history_rows = run_query("SELECT recent_chat FROM conversations WHERE user_id=%s", (uid,), fetch=True)
        recent_chat = history_rows[0][0] if history_rows else ""

        # Intent Classification
        intent = brain.classify_intent(incoming_msg, recent_chat)
        logger.info(f"Intent: {intent}")

        response_text = ""
        if intent == "ADD_EVENT":
            details = brain.extract_event_details(incoming_msg, recent_chat)
            if details and details.get("title") and details.get("datetime"):
                response_text = create_and_verify_event(details["title"], details["datetime"])
            else:
                response_text = "I couldn't quite catch the details for that event. Could you specify the title and time?"
        elif intent == "CANCEL_EVENT":
            response_text = cancel_event(incoming_msg, recent_chat)
        elif intent == "RECALL":
            events, label = get_events_for_query(incoming_msg)
            events_text = "\n".join(events) if events else f"No events found for {label}."
            response_text = brain.generate_response(
                system_instruction=PERSONALITY,
                user_prompt=f"Recall Request: {incoming_msg}\nEvents for {label}:\n{events_text}\n\nRespond to the user about their schedule."
            )
        else:
            response_text = brain.generate_response(PERSONALITY, f"Profile: {profile}\nHistory: {recent_chat}\nUser: {incoming_msg}")

        # Update history
        new_entry = f"User: {incoming_msg}\nJarvis: {response_text}"
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

@app.route("/update_profile", methods=["POST"])
def update_profile():
    """Endpoint to trigger fact extraction and profile update."""
    data = request.json
    uid = data.get("user_id")
    message = data.get("message")
    reply = data.get("reply")

    if not uid or not message or not reply:
        return jsonify({"error": "Missing parameters"}), 400

    profile = load_profile(uid)
    profile_text = format_profile_for_llm(profile)

    facts = brain.extract_facts(message, reply, profile_text, PROFILE_COLUMNS)

    if facts:
        # Update DB logic
        for field, value in facts.items():
            if field in PROFILE_COLUMNS:
                run_query(f"UPDATE profile SET {field} = %s WHERE user_id = %s", (value, uid))
        return jsonify({"status": "updated", "facts": facts})

    return jsonify({"status": "no_new_facts"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
