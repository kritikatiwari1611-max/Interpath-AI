import os
import sys
from pathlib import Path

# Ensure root folder is in sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Load .env if present
env_path = BASE_DIR / ".env"
if env_path.exists():
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

from backend.db import init_db
from database.seed import seed_database
from backend.app import create_app

# Initialize and seed on startup if required
init_db()
seed_database()

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("\n" + "=" * 65)
    print("  >> InternPath AI - Server Running at http://localhost:5000")
    print("  >> Demo Logins:")
    print("     Student (BCA):   student@demo.com  /  Student@123")
    print("     Student (B.Com): priya@demo.com    /  Student@123")
    print("     Admin:           admin@demo.com    /  Admin@123")
    print("=" * 65 + "\n")
    app.run(host="0.0.0.0", port=port, debug=True)
