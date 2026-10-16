from flask import Blueprint, request, jsonify, session
from backend.db import execute_query
from backend.auth_utils import login_required
from backend.services.recommendation_service import get_all_resources

resources_bp = Blueprint("resources", __name__)

@resources_bp.route("/resources", methods=["GET"])
@login_required
def list_resources():
    user_id = session["user_id"]
    resources = get_all_resources()

    # Load completion status for current user
    completed_rows = execute_query(
        "SELECT resource_id, completed FROM resource_progress WHERE user_id = ?",
        (user_id,),
        fetch_all=True
    )
    status_map = {r["resource_id"]: bool(r["completed"]) for r in completed_rows}

    # Enhance resources with per-user completion status
    results = []
    for res in resources:
        item = dict(res)
        item["completed"] = status_map.get(res["id"], False)
        results.append(item)

    return jsonify({"ok": True, "data": results})

@resources_bp.route("/resources/<resource_id>/complete", methods=["PUT"])
@login_required
def toggle_resource(resource_id):
    user_id = session["user_id"]
    data = request.get_json() or {}
    completed = 1 if data.get("completed", True) else 0

    existing = execute_query(
        "SELECT id FROM resource_progress WHERE user_id = ? AND resource_id = ?",
        (user_id, resource_id),
        fetch_one=True
    )
    if existing:
        execute_query(
            "UPDATE resource_progress SET completed = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (completed, existing["id"]),
            commit=True
        )
    else:
        execute_query(
            "INSERT INTO resource_progress (user_id, resource_id, completed) VALUES (?, ?, ?)",
            (user_id, resource_id, completed),
            commit=True
        )

    return jsonify({"ok": True, "data": {"resource_id": resource_id, "completed": bool(completed)}})
