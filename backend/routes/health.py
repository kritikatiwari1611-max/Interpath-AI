from flask import Blueprint, jsonify
from backend.db import execute_query
from backend.config import AI_MODE, OPENAI_API_KEY

health_bp = Blueprint("health", __name__)

@health_bp.route("/health", methods=["GET"])
def health_check():
    db_ok = False
    user_count = 0
    try:
        res = execute_query("SELECT count(*) as count FROM users", fetch_one=True)
        user_count = res["count"] if res else 0
        db_ok = True
    except Exception as e:
        db_ok = False

    ai_status = "OpenAI API" if (AI_MODE == "openai" and bool(OPENAI_API_KEY)) else "Rule-based Demo Mode"

    return jsonify({
        "ok": db_ok,
        "status": "healthy" if db_ok else "unhealthy",
        "database": "connected" if db_ok else "error",
        "user_count": user_count,
        "ai_engine": ai_status,
        "version": "1.0.0"
    }), (200 if db_ok else 500)
