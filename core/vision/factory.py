import os
from core.vision.gemini import GeminiVision

def get_vision_provider():
    provider_type = os.environ.get("VECTA_VISION_PROVIDER", "gemini").lower()

    if provider_type == "gemini":
        return GeminiVision()

    # Placeholder for future local vision models via Ollama or others
    # elif provider_type == "ollama":
    #     return OllamaVision()

    return GeminiVision()

vision_provider = get_vision_provider()
