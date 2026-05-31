import os
from core.intelligence.gemini import GeminiIntelligence
from core.intelligence.ollama import OllamaIntelligence

def get_intelligence():
    provider = os.environ.get("VECTA_LLM_PROVIDER", "gemini").lower()

    if provider == "ollama":
        model = os.environ.get("VECTA_OLLAMA_MODEL", "qwen3:8b")
        return OllamaIntelligence(model_name=model)

    return GeminiIntelligence()

intelligence = get_intelligence()
