import asyncio
import edge_tts
import pygame
import os
import time

class VectaVoice:
    def __init__(self, voice="en-GB-RyanNeural"): # Sophisticated, calm voice
        self.voice = voice
        pygame.mixer.init()

    async def _generate_and_play(self, text):
        communicate = edge_tts.Communicate(text, self.voice)
        temp_file = "response.mp3"
        await communicate.save(temp_file)

        pygame.mixer.music.load(temp_file)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1)

        pygame.mixer.music.unload()
        if os.path.exists(temp_file):
            os.remove(temp_file)

    def speak(self, text):
        print(f"VECTA: {text}")
        try:
            asyncio.run(self._generate_and_play(text))
        except Exception as e:
            print(f"Voice error: {e}")

    def stop(self):
        pygame.mixer.music.stop()

if __name__ == "__main__":
    v = VectaVoice()
    v.speak("Hello Master Wayne. Vecta OS is fully operational.")
