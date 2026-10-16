import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "internpath.db"
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
FRONTEND_DIR = BASE_DIR / "frontend"

# Environment Variables with safe defaults
SECRET_KEY = os.getenv("SECRET_KEY", "internpath-dev-secret-key-change-in-prod")
AI_MODE = os.getenv("AI_MODE", "demo").lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DATABASE_URL = os.getenv("DATABASE_URL", "")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@demo.com")

# Rate limiting and AI quotas
LOGIN_RATE_LIMIT = 5  # attempts
LOGIN_LOCKOUT_MINUTES = 5
AI_DAILY_LIMIT = 30   # calls per user per day
