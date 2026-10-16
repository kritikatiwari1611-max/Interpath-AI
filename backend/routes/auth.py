import time
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from backend.db import execute_query
from backend.auth_utils import login_required, get_current_user
from backend.config import LOGIN_RATE_LIMIT, LOGIN_LOCKOUT_MINUTES

auth_bp = Blueprint("auth", __name__)

# In-memory dictionary tracking failed login attempts: { ip_or_email: {"count": n, "lockout_until": timestamp} }
_FAILED_LOGINS = {}

def is_locked_out(key: str) -> bool:
    info = _FAILED_LOGINS.get(key)
    if not info:
        return False
    if info.get("lockout_until") and datetime.now() < info["lockout_until"]:
        return True
    if info.get("lockout_until") and datetime.now() >= info["lockout_until"]:
        # Reset lockout window
        _FAILED_LOGINS.pop(key, None)
        return False
    return False

def record_failed_attempt(key: str):
    info = _FAILED_LOGINS.setdefault(key, {"count": 0, "lockout_until": None})
    info["count"] += 1
    if info["count"] >= LOGIN_RATE_LIMIT:
        info["lockout_until"] = datetime.now() + timedelta(minutes=LOGIN_LOCKOUT_MINUTES)

def reset_failed_attempts(key: str):
    _FAILED_LOGINS.pop(key, None)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    course = data.get("course", "").strip()
    career_goal = data.get("career_goal", "").strip()

    if not name or not email or not password:
        return jsonify({"ok": False, "error": "Name, email, and password are required."}), 400

    if len(password) < 6:
        return jsonify({"ok": False, "error": "Password must be at least 6 characters long."}), 400

    # Check if user already exists
    existing = execute_query("SELECT id FROM users WHERE email = ?", (email,), fetch_one=True)
    if existing:
        return jsonify({"ok": False, "error": "An account with this email already exists."}), 400

    pw_hash = generate_password_hash(password)
    new_user_id = execute_query(
        "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
        (name, email, pw_hash, "student"),
        commit=True
    )

    # Initialize empty student profile
    execute_query(
        """INSERT INTO student_profiles 
           (user_id, course, career_goal, resume_status, resume_checklist_json, selected_role_id) 
           VALUES (?, ?, ?, 'none', '{}', '')""",
        (new_user_id, course, career_goal),
        commit=True
    )

    # Automatically set session cookie
    session["user_id"] = new_user_id
    session["user_role"] = "student"
    session["user_name"] = name

    return jsonify({
        "ok": True,
        "data": {
            "id": new_user_id,
            "name": name,
            "email": email,
            "role": "student"
        }
    }), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"ok": False, "error": "Email and password are required."}), 400

    # Security: check rate limit lockout
    client_ip = request.remote_addr or "client"
    lockout_key = f"{client_ip}_{email}"
    if is_locked_out(lockout_key):
        return jsonify({
            "ok": False,
            "error": f"Too many failed login attempts. Account temporarily locked for {LOGIN_LOCKOUT_MINUTES} minutes."
        }), 429

    user = execute_query("SELECT id, name, email, password_hash, role FROM users WHERE email = ?", (email,), fetch_one=True)
    if not user or not check_password_hash(user["password_hash"], password):
        record_failed_attempt(lockout_key)
        return jsonify({"ok": False, "error": "Invalid email or password."}), 401

    # Reset failed attempts upon successful login
    reset_failed_attempts(lockout_key)

    session["user_id"] = user["id"]
    session["user_role"] = user["role"]
    session["user_name"] = user["name"]

    return jsonify({
        "ok": True,
        "data": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }
    })

@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True, "data": {"message": "Logged out successfully."}})

@auth_bp.route("/me", methods=["GET"])
def me():
    user = get_current_user()
    if not user:
        return jsonify({"ok": False, "error": "Not authenticated"}), 401
    return jsonify({"ok": True, "data": user})
