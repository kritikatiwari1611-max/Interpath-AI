from flask import Blueprint, request, jsonify, session
from backend.db import execute_query
from backend.auth_utils import login_required
from backend.services.roadmap_service import generate_roadmap

roadmap_bp = Blueprint("roadmap", __name__)

@roadmap_bp.route("/roadmap", methods=["GET"])
@login_required
def get_roadmap():
    user_id = session["user_id"]
    profile = execute_query("SELECT selected_role_id FROM student_profiles WHERE user_id = ?", (user_id,), fetch_one=True)
    role_id = profile.get("selected_role_id") if profile else None

    if not role_id:
        role_id = "python-developer"
        if profile:
            execute_query("UPDATE student_profiles SET selected_role_id = ? WHERE user_id = ?", (role_id, user_id), commit=True)
        else:
            execute_query("INSERT INTO student_profiles (user_id, selected_role_id) VALUES (?, ?)", (user_id, role_id), commit=True)

    user_skills = execute_query("SELECT skill_name, level FROM user_skills WHERE user_id = ?", (user_id,), fetch_all=True)
    
    # Load user's saved task status records
    task_rows = execute_query(
        "SELECT task_key, status FROM roadmap_tasks WHERE user_id = ? AND role_id = ?",
        (user_id, role_id),
        fetch_all=True
    )
    user_tasks_status = {r["task_key"]: r["status"] for r in task_rows}

    roadmap_data = generate_roadmap(role_id, user_skills, user_tasks_status)
    roadmap_data["role_selected"] = True

    return jsonify({"ok": True, "data": roadmap_data})

@roadmap_bp.route("/roadmap/tasks/<task_key>", methods=["PUT"])
@login_required
def update_task_status(task_key):
    user_id = session["user_id"]
    data = request.get_json() or {}
    status = data.get("status", "pending")
    role_id = data.get("role_id", "")

    if not role_id:
        profile = execute_query("SELECT selected_role_id FROM student_profiles WHERE user_id = ?", (user_id,), fetch_one=True)
        role_id = profile.get("selected_role_id", "")

    # Upsert task status
    existing = execute_query(
        "SELECT id FROM roadmap_tasks WHERE user_id = ? AND role_id = ? AND task_key = ?",
        (user_id, role_id, task_key),
        fetch_one=True
    )
    if existing:
        execute_query(
            "UPDATE roadmap_tasks SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, existing["id"]),
            commit=True
        )
    else:
        execute_query(
            "INSERT INTO roadmap_tasks (user_id, role_id, task_key, status) VALUES (?, ?, ?, ?)",
            (user_id, role_id, task_key, status),
            commit=True
        )

    return jsonify({"ok": True, "data": {"task_key": task_key, "status": status}})
