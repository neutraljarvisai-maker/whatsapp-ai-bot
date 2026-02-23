from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.values.get("Body", "").strip()

    resp = MessagingResponse()
    resp.message("AI says: " + incoming_msg)

    return str(resp)

if __name__ == "__main__":
    app.run(port=5000)
