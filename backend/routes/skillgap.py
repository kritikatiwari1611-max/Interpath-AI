from flask import Blueprint, request, jsonify, session
from backend.db import execute_query
from backend.auth_utils import login_required
from backend.services.skill_gap_service import analyze_skill_gap

skillgap_bp = Blueprint("skillgap", __name__)

@skillgap_bp.route("/skill-gap", methods=["GET"])
@login_required
def get_skill_gap():
    user_id = session["user_id"]
    profile = execute_query("SELECT selected_role_id FROM student_profiles WHERE user_id = ?", (user_id,), fetch_one=True)
    role_id = profile.get("selected_role_id") if profile else None

    if not role_id:
        return jsonify({
            "ok": True,
            "data": {
                "role_selected": False,
                "message": "No internship role selected. Please choose a target role first."
            }
        })

    user_skills = execute_query("SELECT skill_name, level FROM user_skills WHERE user_id = ?", (user_id,), fetch_all=True)
    gap_result = analyze_skill_gap(role_id, user_skills)
    gap_result["role_selected"] = True

    return jsonify({"ok": True, "data": gap_result})

@skillgap_bp.route("/skills", methods=["PUT"])
@skillgap_bp.route("/skill-gap/skills", methods=["PUT"])
@login_required
def update_skills():
    """Batch updates or replaces student skills."""
    user_id = session["user_id"]
    data = request.get_json() or {}
    skills_list = data.get("skills", [])

    # Replace user skills
    execute_query("DELETE FROM user_skills WHERE user_id = ?", (user_id,), commit=True)
    for s in skills_list:
        name = s.get("name", "").strip()
        level = s.get("level", "Beginner").strip()
        if name:
            execute_query(
                "INSERT INTO user_skills (user_id, skill_name, level) VALUES (?, ?, ?)",
                (user_id, name, level),
                commit=True
            )

    return jsonify({"ok": True, "data": {"message": "Skills updated successfully."}})
