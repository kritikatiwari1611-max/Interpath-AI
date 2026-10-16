from flask import Blueprint, jsonify, session, request
from backend.db import execute_query
from backend.auth_utils import login_required

settings_bp = Blueprint("settings", __name__)

@settings_bp.route("/settings/reset", methods=["POST"])
@login_required
def reset_student_data():
    """Resets progress, tasks, test attempts, and skills back to default demo state."""
    user_id = session["user_id"]

    # Clear user activity tables
    execute_query("DELETE FROM roadmap_tasks WHERE user_id = ?", (user_id,), commit=True)
    execute_query("DELETE FROM resource_progress WHERE user_id = ?", (user_id,), commit=True)
    execute_query("DELETE FROM project_progress WHERE user_id = ?", (user_id,), commit=True)
    execute_query("DELETE FROM interview_attempts WHERE user_id = ?", (user_id,), commit=True)
    execute_query("DELETE FROM mock_interviews WHERE user_id = ?", (user_id,), commit=True)
    execute_query("DELETE FROM readiness_snapshots WHERE user_id = ?", (user_id,), commit=True)
    execute_query("DELETE FROM notifications WHERE user_id = ?", (user_id,), commit=True)

    return jsonify({"ok": True, "data": {"message": "Your demo progress and test records have been reset."}})

@settings_bp.route("/settings/delete-account", methods=["POST"])
@login_required
def delete_account():
    """Privacy requirement (Phase 9b): Complete deletion of account and all associated data."""
    user_id = session["user_id"]
    
    # Delete cascades to all profile, skill, progress, and interview records
    execute_query("DELETE FROM users WHERE id = ?", (user_id,), commit=True)
    session.clear()
    
    return jsonify({"ok": True, "data": {"message": "Your account and all associated data have been permanently removed."}})
