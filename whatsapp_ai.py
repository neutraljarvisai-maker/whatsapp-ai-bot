from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

# Root route for browser test
@app.route("/")
def home():
    return "Bot is running!"

# Debug WhatsApp webhook
@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    # Get the incoming message from Twilio
    incoming_msg = request.values.get('Body', '')
    from_number = request.values.get('From', '')
    
    # Print to Railway logs for debugging
    print(f"Incoming message from {from_number}: {incoming_msg}")
    
    # Fixed debug reply
    resp = MessagingResponse()
    resp.message(f"Hello! I received your message: '{incoming_msg}'")
    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)
