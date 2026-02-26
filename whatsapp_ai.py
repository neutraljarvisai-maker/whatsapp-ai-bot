@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():

    data = request.form
    user_id = data.get("From")
    user_message = (data.get("Body") or "").strip()

    if not user_id or not user_message:
        return "OK", 200

    lower_msg = user_message.lower()

    # -------------------------------------------------
    # SHORT / LONG RESPONSE MODE
    # -------------------------------------------------
    if "short" in lower_msg and "answer" in lower_msg:
        update_profile(user_id, "response_style: short")
        resp = MessagingResponse()
        resp.message("👍 I’ll keep replies short.")
        return str(resp)

    if "long" in lower_msg or "detailed" in lower_msg:
        update_profile(user_id, "response_style: long")
        resp = MessagingResponse()
        resp.message("👍 I’ll give detailed replies.")
        return str(resp)

    # -------------------------------------------------
    # SIMPLE SMALL TALK
    # -------------------------------------------------
    if lower_msg in ["hi", "hello", "hey"]:
        resp = MessagingResponse()
        resp.message("Hey 👋")
        return str(resp)

    if lower_msg in ["ok", "okay", "k"]:
        resp = MessagingResponse()
        resp.message("👍")
        return str(resp)

    # -------------------------------------------------
    # GET MEMORY & PROFILE
    # -------------------------------------------------
    chat_history = get_memory(user_id)
    profile_facts = get_profile(user_id)

    style = "short" if "response_style: short" in profile_facts else "normal"

    # Limit chat history
    history_lines = chat_history.split("\n")[-8:]
    limited_history = "\n".join(history_lines)

    # -------------------------------------------------
    # ⭐ SMART MEMORY RECALL
    # -------------------------------------------------
    relevant_memories = get_relevant_memories(user_id, user_message)

    # -------------------------------------------------
    # LEARNING (only for meaningful messages)
    # -------------------------------------------------
    if len(user_message.split()) > 3:

        updated_facts = extract_facts(profile_facts, user_message)
        update_profile(user_id, updated_facts)

        task = extract_task_from_message(user_message)
        if task and task.upper() != "NONE":
            add_task(user_id, task)

        interests = extract_interests(user_message)
        update_interests(user_id, interests)

    else:
        updated_facts = profile_facts

    # -------------------------------------------------
    # BUILD PROMPT
    # -------------------------------------------------
    if style == "short":
        style_instruction = "Reply VERY briefly. 1–2 short sentences."
    else:
        style_instruction = "Reply normally."

    prompt = f"""
You are Jarvis, a calm intelligent AI assistant.

{style_instruction}

Relevant memories:
{relevant_memories}

Recent conversation:
{limited_history}

User: {user_message}
Jarvis:
"""

    ai_response = ask_groq(prompt, updated_facts)

    # -------------------------------------------------
    # UPDATE MEMORY
    # -------------------------------------------------
    new_history = f"{limited_history}\nUser: {user_message}\nJarvis: {ai_response}"
    update_memory(user_id, new_history)

    resp = MessagingResponse()
    resp.message(ai_response)

    return str(resp)
