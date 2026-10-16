import json
from flask import Blueprint, request, jsonify, session
from backend.db import execute_query
from backend.auth_utils import login_required

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/profile", methods=["GET"])
@login_required
def get_profile():
    user_id = session["user_id"]
    profile = execute_query("SELECT * FROM student_profiles WHERE user_id = ?", (user_id,), fetch_one=True)
    if not profile:
        profile = {
            "course": "", "specialization": "", "semester": "", "college": "",
            "career_goal": "", "interests": "", "resume_status": "none",
            "resume_checklist_json": "{}", "github_link": "", "selected_role_id": ""
        }
    
    # Parse checklist JSON safely
    try:
        checklist = json.loads(profile.get("resume_checklist_json") or "{}")
    except Exception:
        checklist = {}

    # Fetch skills, projects, and certifications
    skills = execute_query("SELECT id, skill_name, level FROM user_skills WHERE user_id = ?", (user_id,), fetch_all=True)
    projects = execute_query("SELECT id, title, description, tech, status FROM user_projects WHERE user_id = ?", (user_id,), fetch_all=True)
    certs = execute_query("SELECT id, title, issuer FROM user_certifications WHERE user_id = ?", (user_id,), fetch_all=True)

    return jsonify({
        "ok": True,
        "data": {
            "profile": {
                "course": profile.get("course", ""),
                "specialization": profile.get("specialization", ""),
                "semester": profile.get("semester", ""),
                "college": profile.get("college", ""),
                "career_goal": profile.get("career_goal", ""),
                "interests": profile.get("interests", ""),
                "resume_status": profile.get("resume_status", "none"),
                "resume_checklist": checklist,
                "github_link": profile.get("github_link", ""),
                "selected_role_id": profile.get("selected_role_id", "")
            },
            "skills": skills,
            "projects": projects,
            "certifications": certs
        }
    })

@profile_bp.route("/profile", methods=["PUT"])
@login_required
def update_profile():
    user_id = session["user_id"]
    data = request.get_json() or {}

    course = data.get("course", "").strip()
    specialization = data.get("specialization", "").strip()
    semester = data.get("semester", "").strip()
    college = data.get("college", "").strip()
    career_goal = data.get("career_goal", "").strip()
    interests = data.get("interests", "").strip()
    resume_status = data.get("resume_status", "none")
    resume_checklist = json.dumps(data.get("resume_checklist", {}))
    github_link = data.get("github_link", "").strip()
    selected_role_id = data.get("selected_role_id", "").strip()

    # Upsert student profile
    existing = execute_query("SELECT user_id FROM student_profiles WHERE user_id = ?", (user_id,), fetch_one=True)
    if existing:
        execute_query(
            """UPDATE student_profiles SET 
               course = ?, specialization = ?, semester = ?, college = ?, career_goal = ?, 
               interests = ?, resume_status = ?, resume_checklist_json = ?, github_link = ?, 
               selected_role_id = ? 
               WHERE user_id = ?""",
            (course, specialization, semester, college, career_goal, interests, resume_status, resume_checklist, github_link, selected_role_id, user_id),
            commit=True
        )
    else:
        execute_query(
            """INSERT INTO student_profiles 
               (user_id, course, specialization, semester, college, career_goal, interests, resume_status, resume_checklist_json, github_link, selected_role_id) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, course, specialization, semester, college, career_goal, interests, resume_status, resume_checklist, github_link, selected_role_id),
            commit=True
        )

    return jsonify({"ok": True, "data": {"message": "Profile updated successfully."}})

@profile_bp.route("/profile/role", methods=["PUT"])
@login_required
def update_selected_role():
    user_id = session["user_id"]
    data = request.get_json() or {}
    role_id = data.get("role_id", "").strip()

    execute_query("UPDATE student_profiles SET selected_role_id = ? WHERE user_id = ?", (role_id, user_id), commit=True)
    return jsonify({"ok": True, "data": {"selected_role_id": role_id}})
