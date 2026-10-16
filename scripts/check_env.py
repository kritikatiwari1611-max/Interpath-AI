import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

def check_env():
    print("=" * 60)
    print("      InternPath AI - Environment Settings Check (Safe)     ")
    print("=" * 60)
    print("Note: In accordance with security rules, secret values are NEVER printed.\n")
    
    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        print("[!] .env file is MISSING at project root.")
        return False
    else:
        print("[OK] .env file found.")

    # Load environment variables manually if not in os.environ
    env_vars = {}
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env_vars[k.strip()] = v.strip()

    settings_to_check = [
        ("SECRET_KEY", True),          # (name, is_secret)
        ("AI_MODE", False),
        ("OPENAI_API_KEY", True),
        ("OPENAI_MODEL", False),
        ("DATABASE_URL", True),
        ("ADMIN_EMAIL", False)
    ]
    
    for key, is_secret in settings_to_check:
        val = env_vars.get(key, os.getenv(key, ""))
        status = "SET [CONFIDENTIAL]" if is_secret and val else ("SET (" + val + ")" if not is_secret and val else "MISSING / EMPTY")
        indicator = "[OK]" if val else ("[INFO]" if key in ("OPENAI_API_KEY", "DATABASE_URL") else "[MISSING]")
        print(f" {indicator:<8} {key:<18}: {status}")

    print("-" * 60)
    db_mode = "Supabase / PostgreSQL" if env_vars.get("DATABASE_URL") else "Local SQLite (internpath.db)"
    print(f" Active Database Target : {db_mode}")
    ai_mode = env_vars.get("AI_MODE", "demo")
    has_key = bool(env_vars.get("OPENAI_API_KEY"))
    effective_ai = "OpenAI API" if (ai_mode == "openai" and has_key) else "Offline Demo Mode (Rule-based)"
    print(f" Effective AI Engine    : {effective_ai}")
    print("=" * 60)
    return True

if __name__ == "__main__":
    check_env()
