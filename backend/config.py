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

# -----------------------------------------------------------------------------
# CENTRAL CONFIGURATION FOR GUIDED FLOW & CONSTANTS (Section 9)
# -----------------------------------------------------------------------------
# Skill proficiency levels and numerical multipliers: Low (0.4), Medium (0.7), High (1.0)
SKILL_LEVELS = {
    "Low": 0.4,
    "Medium": 0.7,
    "High": 1.0,
    "low": 0.4,
    "medium": 0.7,
    "high": 1.0,
    # Backward compatibility with legacy entries:
    "beginner": 0.4,
    "intermediate": 0.7,
    "advanced": 1.0,
    "Beginner": 0.4,
    "Intermediate": 0.7,
    "Advanced": 1.0
}

# Standardized task, resource, and project status values
STATUS_PENDING = "pending"
STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETED = "completed"
STATUS_SAVED = "saved"

VALID_STATUSES = [STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_COMPLETED]

# Deterministic threshold for "You are ready to apply" message
READINESS_APPLY_THRESHOLD = 65

# Secure user uploads directory
UPLOADS_DIR = BASE_DIR / "uploads"
MAX_UPLOAD_SIZE_BYTES = 2 * 1024 * 1024  # 2 Megabytes
ALLOWED_EXTENSIONS = {"pdf", "docx"}

