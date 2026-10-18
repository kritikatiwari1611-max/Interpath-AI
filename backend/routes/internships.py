from flask import Blueprint, jsonify, session
from backend.db import execute_query
from backend.auth_utils import login_required
from backend.services.matching_service import match_internships

internships_bp = Blueprint("internships", __name__)

@internships_bp.route("/internships", methods=["GET"])
@login_required
def get_matched_internships():
    user_id = session["user_id"]
    profile = execute_query(
        "SELECT selected_role_id, interests, resume_filename, linkedin_link, github_link FROM student_profiles WHERE user_id = ?",
        (user_id,),
        fetch_one=True
    )
    role_id = profile.get("selected_role_id", "") if profile else ""
    interests = profile.get("interests", "") if profile else ""

    user_skills = execute_query("SELECT skill_name, level FROM user_skills WHERE user_id = ?", (user_id,), fetch_all=True)

    matches = match_internships(role_id, user_skills, interests)

    application_readiness = {
        "resume_uploaded": bool(profile and profile.get("resume_filename")),
        "linkedin_added": bool(profile and profile.get("linkedin_link")),
        "github_added": bool(profile and profile.get("github_link")),
        "all_ready": bool(profile and profile.get("resume_filename") and profile.get("linkedin_link") and profile.get("github_link"))
    }

    return jsonify({
        "ok": True,
        "data": {
            "role_id": role_id,
            "internships": matches,
            "application_readiness": application_readiness,
            "disclaimer": "Demo data, not live vacancies. No application is submitted to external servers."
        }
    })

