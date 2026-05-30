from flask import Flask, request, jsonify
from flask_cors import CORS
from vecta_os.agents.coordinator import coordinator
from vecta_os.core.brain import brain
from vecta_os.services.profile_util import load_profile, format_profile_for_llm
from vecta_os.services.database import db
from vecta_os.services.calendar_util import create_and_verify_event, get_events_for_query
from vecta_os.scheduler.scheduler import scheduler
from twilio.twiml.messaging_response import MessagingResponse
import os
import uuid
import logging

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "active", "system": "VECTA CLOUD OS v3.0"})

@app.route("/api/v1/chat", methods=["POST"])
def chat():
    """Unified chat endpoint for VECTA CLOUD OS."""
    data = request.json
    user_input = data.get("message")
    user_id = data.get("user_id", "default")

    # Load Context
    profile = load_profile(user_id)
    profile_text = format_profile_for_llm(profile)

    # Run through Coordinator
    result = coordinator.run(user_input, context={"user_id": user_id, "profile": profile_text})

    # Extract Facts/Events from Coordinator result
    intent = result.get("intent")
    facts = result.get("facts", {})
    event = result.get("event", {})

    if facts:
        for field, val in facts.items():
            db.run_query(f"UPDATE profile SET {field} = %s WHERE user_id = %s", (val, user_id))

    if intent == "ADD_EVENT" and event:
        create_and_verify_event(event.get("title", "Task"), event.get("datetime", ""))

    return jsonify(result)

@app.route("/api/v1/plan_action", methods=["POST"])
def plan_action():
    """Vision-based ReAct planning endpoint."""
    if 'screenshot' not in request.files:
        return jsonify({"error": "No screenshot"}), 400

    screenshot = request.files['screenshot']
    task = request.form.get("task")
    user_id = request.form.get("user_id")
    history = request.form.get("history", "").split("|")

    temp_path = f"/tmp/{uuid.uuid4()}.png"
    screenshot.save(temp_path)

    try:
        action_result = brain.analyze_screen_and_plan(temp_path, task, history)
        return jsonify({"action": action_result})
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)

@app.route("/api/v1/whatsapp", methods=["POST"])
def whatsapp():
    """VECTA WhatsApp Channel support."""
    form_data = request.form
    uid = form_data.get("From")
    msg = form_data.get("Body", "").strip()

    if not uid: return "OK"

    # Process via Coordinator
    result = coordinator.run(msg, context={"user_id": uid, "channel": "whatsapp"})
    resp_text = result.get("response", "VECTA is processing...")

    if result.get("intent") == "RECALL":
        events, label = get_events_for_query(msg)
        if events: resp_text += f"\n\nSchedule for {label}:\n" + "\n".join(events)

    twiml = MessagingResponse()
    twiml.message(resp_text)
    return str(twiml)

if __name__ == "__main__":
    scheduler.start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
