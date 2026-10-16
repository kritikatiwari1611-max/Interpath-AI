import os
import sys
import secrets
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

def run_wizard():
    print("=" * 60)
    print("      InternPath AI - Quick Setup & Onboarding Wizard       ")
    print("=" * 60)
    
    env_file = BASE_DIR / ".env"
    env_example = BASE_DIR / ".env.example"
    
    if not env_file.exists():
        print("[1/4] Creating .env from .env.example...")
        if env_example.exists():
            with open(env_example, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            content = "SECRET_KEY=default\nAI_MODE=demo\n"
        
        # Generate secure random secret key
        gen_secret = secrets.token_hex(24)
        content = content.replace("change-this-in-production-random-secret-key-internpath", gen_secret)
        
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(" -> Generated .env with a secure random SECRET_KEY.")
    else:
        print("[1/4] Existing .env file detected.")
        
    print("\n[2/4] Testing Database connection & Initializing Schema...")
    try:
        from backend.db import init_db
        init_db()
        print(" -> Database schema initialized successfully.")
    except Exception as e:
        print(f" -> ERROR: Database initialization failed: {e}")
        return False
        
    print("\n[3/4] Seeding initial demo student and admin accounts...")
    try:
        from database.seed import seed_database
        seed_database()
        print(" -> Seed data populated.")
    except Exception as e:
        print(f" -> ERROR: Seeding failed: {e}")
        return False

    print("\n[4/4] Performing application health test...")
    try:
        from backend.db import execute_query
        u_count = execute_query("SELECT count(*) as count FROM users;", fetch_one=True)
        print(f" -> Health OK! Database holds {u_count['count']} users.")
    except Exception as e:
        print(f" -> ERROR during health test: {e}")
        return False

    print("\n" + "=" * 60)
    print(" Setup Complete! You can now start InternPath AI with:")
    print("   python run.py")
    print("   or run start.bat (Windows) / bash start.sh (Mac/Linux)")
    print("=" * 60)
    return True

if __name__ == "__main__":
    run_wizard()
