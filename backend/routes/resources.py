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

    # Load completion and status for current user
    progress_rows = execute_query(
        "SELECT resource_id, completed, status FROM resource_progress WHERE user_id = ?",
        (user_id,),
        fetch_all=True
    )
    status_map = {}
    completed_map = {}
    for r in progress_rows:
        rid = r["resource_id"]
        st = r.get("status") or ("completed" if r.get("completed") else "pending")
        status_map[rid] = st
        completed_map[rid] = (st == "completed" or bool(r.get("completed")))

    # Enhance resources with per-user completion & status
    results = []
    for res in resources:
        item = dict(res)
        rid = res["id"]
        item["status"] = status_map.get(rid, "pending")
        item["completed"] = completed_map.get(rid, False)
        results.append(item)

    return jsonify({"ok": True, "data": results})

@resources_bp.route("/resources/<resource_id>/complete", methods=["PUT"])
@login_required
def toggle_resource(resource_id):
    user_id = session["user_id"]
    data = request.get_json() or {}
    completed = 1 if data.get("completed", True) else 0
    status = "completed" if completed else "pending"

    existing = execute_query(
        "SELECT id FROM resource_progress WHERE user_id = ? AND resource_id = ?",
        (user_id, resource_id),
        fetch_one=True
    )
    if existing:
        execute_query(
            "UPDATE resource_progress SET completed = ?, status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (completed, status, existing["id"]),
            commit=True
        )
    else:
        execute_query(
            "INSERT INTO resource_progress (user_id, resource_id, completed, status) VALUES (?, ?, ?, ?)",
            (user_id, resource_id, completed, status),
            commit=True
        )

    return jsonify({"ok": True, "data": {"resource_id": resource_id, "completed": bool(completed), "status": status}})

@resources_bp.route("/resources/<resource_id>/status", methods=["PUT"])
@login_required
def set_resource_status(resource_id):
    """Sets segmented 3-status (pending, in_progress, completed) for a resource."""
    user_id = session["user_id"]
    data = request.get_json() or {}
    status = data.get("status", "pending")
    if status not in ("pending", "in_progress", "completed"):
        status = "pending"
    completed = 1 if status == "completed" else 0

    existing = execute_query(
        "SELECT id FROM resource_progress WHERE user_id = ? AND resource_id = ?",
        (user_id, resource_id),
        fetch_one=True
    )
    if existing:
        execute_query(
            "UPDATE resource_progress SET status = ?, completed = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, completed, existing["id"]),
            commit=True
        )
    else:
        execute_query(
            "INSERT INTO resource_progress (user_id, resource_id, status, completed) VALUES (?, ?, ?, ?)",
            (user_id, resource_id, status, completed),
            commit=True
        )

    return jsonify({"ok": True, "data": {"resource_id": resource_id, "status": status, "completed": bool(completed)}})
