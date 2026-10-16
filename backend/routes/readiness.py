import json
from flask import Blueprint, jsonify, session, request
from backend.db import execute_query
from backend.auth_utils import login_required
from backend.services.role_helper import get_role_by_id
from backend.services.readiness_service import calculate_readiness_score
from backend.services.ai_service import generate_ai_summary

readiness_bp = Blueprint("readiness", __name__)

@readiness_bp.route("/readiness", methods=["GET"])
@login_required
def get_readiness():
    user_id = session["user_id"]
    profile = execute_query("SELECT selected_role_id, resume_checklist_json FROM student_profiles WHERE user_id = ?", (user_id,), fetch_one=True)
    role_id = profile.get("selected_role_id") if profile else None

    user_skills = execute_query("SELECT skill_name, level FROM user_skills WHERE user_id = ?", (user_id,), fetch_all=True)
    user_projects = execute_query("SELECT title, description, tech, status FROM user_projects WHERE user_id = ?", (user_id,), fetch_all=True)
    user_certs = execute_query("SELECT title, issuer FROM user_certifications WHERE user_id = ?", (user_id,), fetch_all=True)
    
    # Checklist
    try:
        resume_checklist = json.loads(profile.get("resume_checklist_json") or "{}") if profile else {}
    except Exception:
        resume_checklist = {}

    # Interview activity
    attempts = execute_query("SELECT is_correct FROM interview_attempts WHERE user_id = ?", (user_id,), fetch_all=True)
    mocks = execute_query("SELECT id FROM mock_interviews WHERE user_id = ?", (user_id,), fetch_all=True)
    
    total_att = len(attempts)
    correct_att = sum(1 for a in attempts if a["is_correct"] == 1)
    accuracy = round((correct_att / total_att * 100), 1) if total_att > 0 else 0.0

    interview_stats = {
        "total_attempts": total_att,
        "accuracy": accuracy,
        "mock_interviews_done": len(mocks)
    }

    role_meta = get_role_by_id(role_id) if role_id else None
    readiness = calculate_readiness_score(
        role_id=role_id,
        user_skills=user_skills,
        user_projects=user_projects,
        resume_checklist=resume_checklist,
        interview_stats=interview_stats,
        user_certifications=user_certs,
        role_meta=role_meta
    )

    # Save snapshot to database
    execute_query(
        """INSERT INTO readiness_snapshots (user_id, role_id, overall, breakdown_json, provisional) 
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, role_id or "none", readiness["overall"], json.dumps(readiness["category_scores"]), 1 if readiness["provisional"] else 0),
        commit=True
    )

    # Optional AI narrative summary (language query parameter: en / hi)
    lang = request.args.get("lang", "en")
    ai_feedback = generate_ai_summary(
        role_title=role_meta.get("title") if role_meta else "Chosen Career Track",
        readiness_score=readiness["overall"],
        skills=user_skills,
        language=lang
    )
    readiness["ai_feedback"] = ai_feedback

    return jsonify({"ok": True, "data": readiness})
