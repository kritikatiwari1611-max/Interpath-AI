from functools import wraps
from flask import session, jsonify, request
from backend.db import execute_query

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"ok": False, "error": "Authentication required. Please log in."}), 401
        return f(*args, **kwargs)
    return decorated_function

def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get("user_id")
            if not user_id:
                return jsonify({"ok": False, "error": "Authentication required. Please log in."}), 401
            
            user = execute_query("SELECT role FROM users WHERE id = ?", (user_id,), fetch_one=True)
            if not user or user["role"] != required_role:
                return jsonify({"ok": False, "error": f"Access forbidden. '{required_role}' privileges required."}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return execute_query("SELECT id, name, email, role, created_at FROM users WHERE id = ?", (user_id,), fetch_one=True)
