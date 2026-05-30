import os
from typing import Dict, Any

class Config:
    def __init__(self):
        # API Keys
        self.GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
        self.GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
        self.SUPABASE_URL = os.environ.get("SUPABASE_URL")
        self.DATABASE_URL = os.environ.get("DATABASE_URL")

        # System Settings
        self.VERSION = "3.0.0"
        self.SYSTEM_NAME = "VECTA CLOUD OS"
        self.DEFAULT_MODEL = "gemini-2.0-flash-exp"

        # Paths
        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.SKILLS_DIR = os.path.join(self.BASE_DIR, "skills")

config = Config()
