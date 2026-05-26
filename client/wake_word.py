import os
import sys
import json
import wave
import requests
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer

# Configuration
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}

config = load_config()
VOSK_MODEL_PATH = os.environ.get("VOSK_MODEL_PATH", config.get("VOSK_MODEL_PATH", "model"))
BACKEND_URL = os.environ.get("JARVIS_BACKEND_URL", config.get("JARVIS_BACKEND_URL", "http://localhost:5000"))
USER_ID = os.environ.get("JARVIS_USER_ID", config.get("JARVIS_USER_ID", "default_user"))

class WakeWordDetector:
    def __init__(self, model_path=VOSK_MODEL_PATH):
        if not os.path.exists(model_path):
            print(f"Please download a Vosk model from https://alphacephei.com/vosk/models and unpack as '{model_path}'")
            self.model = None
        else:
            self.model = Model(model_path)
            self.q = queue.Queue()

    def callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            print(status, file=sys.stderr)
        self.q.put(bytes(indata))

    def listen(self, callback_on_wake):
        if not self.model: return

        device_info = sd.query_devices(None, 'input')
        samplerate = int(device_info['default_samplerate'])

        with sd.RawInputStream(samplerate=samplerate, blocksize=8000, device=None, dtype='int16',
                                channels=1, callback=self.callback):
            rec = KaldiRecognizer(self.model, samplerate)
            print("Listening for 'Hey Vecta'...")

            while True:
                data = self.q.get()
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "")
                    print(f"Recognized: {text}")
                    if "hey vecta" in text or "vecta" in text:
                        print("Wake word detected!")
                        callback_on_wake()
                else:
                    # Partial result
                    pass

if __name__ == "__main__":
    def on_wake():
        print("YES SIR?")

    detector = WakeWordDetector()
    detector.listen(on_wake)
