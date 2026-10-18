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

    custom_rows = execute_query(
        "SELECT id, title, description, tech, status, github_link, demo_link, report_filename, report_original_name FROM user_projects WHERE user_id = ? ORDER BY id DESC",
        (user_id,),
        fetch_all=True
    )

    return jsonify({"ok": True, "data": results, "custom_projects": custom_rows})

@projects_bp.route("/projects/custom", methods=["GET"])
@login_required
def get_custom_projects():
    user_id = session["user_id"]
    custom_rows = execute_query(
        "SELECT id, title, description, tech, status, github_link, demo_link, report_filename, report_original_name FROM user_projects WHERE user_id = ? ORDER BY id DESC",
        (user_id,),
        fetch_all=True
    )
    return jsonify({"ok": True, "data": custom_rows})

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

@projects_bp.route("/projects/custom", methods=["POST"])
@login_required
def create_custom_project():
    """Adds a student's own project with optional github, demo, and pdf documentation."""
    import secrets
    from werkzeug.utils import secure_filename
    from backend.config import UPLOADS_DIR, MAX_UPLOAD_SIZE_BYTES

    user_id = session["user_id"]
    
    # Can receive form-data or JSON
    if request.content_type and "multipart/form-data" in request.content_type:
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        tech = request.form.get("tech", "").strip()
        status = request.form.get("status", "completed").strip()
        github_link = request.form.get("github_link", "").strip()
        demo_link = request.form.get("demo_link", "").strip()
        report_file = request.files.get("report_file")
    else:
        data = request.get_json() or {}
        title = data.get("title", "").strip()
        description = data.get("description", "").strip()
        tech = data.get("tech", "").strip()
        status = data.get("status", "completed").strip()
        github_link = data.get("github_link", "").strip()
        demo_link = data.get("demo_link", "").strip()
        report_file = None

    if not title:
        return jsonify({"ok": False, "error": "Project title is required."}), 400
    if not description:
        return jsonify({"ok": False, "error": "Project description is required."}), 400
    if len(description) > 500:
        return jsonify({"ok": False, "error": "Description cannot exceed 500 characters."}), 400

    if github_link and not github_link.startswith("https://github.com/"):
        return jsonify({"ok": False, "error": "GitHub repository URL must start with https://github.com/"}), 400

    report_filename = ""
    report_original_name = ""

    if report_file and report_file.filename != "":
        fname = secure_filename(report_file.filename)
        ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
        if ext != "pdf":
            return jsonify({"ok": False, "error": "Project report must be a .pdf document only."}), 400

        content = report_file.read()
        if len(content) > MAX_UPLOAD_SIZE_BYTES:
            return jsonify({"ok": False, "error": "File size exceeds 2 MB limit."}), 400

        user_folder = UPLOADS_DIR / str(user_id)
        user_folder.mkdir(parents=True, exist_ok=True)
        report_filename = f"proj_{secrets.token_hex(10)}.pdf"
        with open(user_folder / report_filename, "wb") as f:
            f.write(content)
        report_original_name = fname

    new_id = execute_query(
        """INSERT INTO user_projects (user_id, title, description, tech, status, github_link, demo_link, report_filename, report_original_name)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, title, description, tech, status, github_link, demo_link, report_filename, report_original_name),
        commit=True
    )

    return jsonify({
        "ok": True,
        "data": {
            "id": new_id,
            "title": title,
            "message": "Custom project saved successfully."
        }
    }), 201

@projects_bp.route("/projects/custom/<int:proj_id>", methods=["DELETE"])
@login_required
def delete_custom_project(proj_id):
    user_id = session["user_id"]
    execute_query("DELETE FROM user_projects WHERE id = ? AND user_id = ?", (proj_id, user_id), commit=True)
    return jsonify({"ok": True, "data": {"message": "Project deleted."}})

@projects_bp.route("/projects/custom/<int:proj_id>/status", methods=["PUT"])
@login_required
def update_custom_project_status(proj_id):
    user_id = session["user_id"]
    data = request.get_json() or {}
    status = data.get("status", "completed").strip()
    execute_query("UPDATE user_projects SET status = ? WHERE id = ? AND user_id = ?", (status, proj_id, user_id), commit=True)
    return jsonify({"ok": True, "data": {"id": proj_id, "status": status}})

