import json
from flask import Blueprint, request, jsonify, session
from backend.db import execute_query
from backend.auth_utils import login_required
from backend.services.recommendation_service import get_all_projects

projects_bp = Blueprint("projects", __name__)

@projects_bp.route("/projects", methods=["GET"])
@login_required
def list_projects():
    user_id = session["user_id"]
    profile = execute_query("SELECT selected_role_id FROM student_profiles WHERE user_id = ?", (user_id,), fetch_one=True)
    role_id = profile.get("selected_role_id") if profile else None

    all_proj = get_all_projects()
    
    # Progress records for this student
    progress_rows = execute_query(
        "SELECT project_id, status, milestones_done FROM project_progress WHERE user_id = ?",
        (user_id,),
        fetch_all=True
    )
    status_map = {}
    for r in progress_rows:
        try:
            m_done = json.loads(r.get("milestones_done") or "[]")
        except Exception:
            m_done = []
        status_map[r["project_id"]] = {
            "status": r["status"],
            "milestones_done": m_done
        }

    results = []
    for p in all_proj:
        item = dict(p)
        prog = status_map.get(p["id"], {"status": "saved", "milestones_done": []})
        item["status"] = prog["status"]
        item["milestones_done"] = prog["milestones_done"]
        item["is_recommended"] = (p.get("role_id") == role_id)
        results.append(item)

    return jsonify({"ok": True, "data": results})

@projects_bp.route("/projects/<project_id>/status", methods=["PUT"])
@login_required
def update_project_status(project_id):
    user_id = session["user_id"]
    data = request.get_json() or {}
    status = data.get("status", "saved")
    milestones_done = json.dumps(data.get("milestones_done", []))

    existing = execute_query(
        "SELECT id FROM project_progress WHERE user_id = ? AND project_id = ?",
        (user_id, project_id),
        fetch_one=True
    )
    if existing:
        execute_query(
            "UPDATE project_progress SET status = ?, milestones_done = ? WHERE id = ?",
            (status, milestones_done, existing["id"]),
            commit=True
        )
    else:
        execute_query(
            "INSERT INTO project_progress (user_id, project_id, status, milestones_done) VALUES (?, ?, ?, ?)",
            (user_id, project_id, status, milestones_done),
            commit=True
        )

    return jsonify({"ok": True, "data": {"project_id": project_id, "status": status}})
