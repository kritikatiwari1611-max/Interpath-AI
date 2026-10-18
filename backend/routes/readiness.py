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
    profile = execute_query(
        "SELECT selected_role_id, resume_checklist_json, resume_filename, linkedin_link, github_link FROM student_profiles WHERE user_id = ?",
        (user_id,),
        fetch_one=True
    )
    role_id = profile.get("selected_role_id") if profile else None

    user_skills = execute_query("SELECT skill_name, level FROM user_skills WHERE user_id = ?", (user_id,), fetch_all=True)
    user_projects = execute_query("SELECT title, description, tech, status FROM user_projects WHERE user_id = ?", (user_id,), fetch_all=True)
    user_certs = execute_query("SELECT title, issuer FROM user_certifications WHERE user_id = ?", (user_id,), fetch_all=True)
    
    # Checklist
    try:
        resume_checklist = json.loads(profile.get("resume_checklist_json") or "{}") if profile else {}
    except Exception:
        resume_checklist = {}

    # If resume file uploaded or links provided, auto-tick existence checklist
    if profile and profile.get("resume_filename"):
        resume_checklist["resume_exists"] = True
    if profile and (profile.get("linkedin_link") or profile.get("github_link")):
        resume_checklist["contact_portfolio_links"] = True

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

    # Query Roadmap tasks stats for this user
    roadmap_tasks = execute_query(
        "SELECT status FROM roadmap_tasks WHERE user_id = ? AND role_id = ?",
        (user_id, role_id or ""),
        fetch_all=True
    )
    total_rm_tasks = len(roadmap_tasks)
    done_rm_tasks = sum(1 for t in roadmap_tasks if t["status"] == "completed")

    # Detailed query for resources completed
    res_completed_count = execute_query(
        "SELECT count(*) as c FROM resource_progress WHERE user_id = ? AND (completed = 1 OR status = 'completed')",
        (user_id,),
        fetch_one=True
    )
    res_done_num = res_completed_count["c"] if res_completed_count else 0

    # Foundation stage started check
    found_started_row = execute_query(
        "SELECT count(*) as c FROM roadmap_tasks WHERE user_id = ? AND task_key LIKE 'st1_%' AND status IN ('in_progress', 'completed')",
        (user_id,),
        fetch_one=True
    )
    foundation_started = (found_started_row and found_started_row["c"] > 0) or (done_rm_tasks > 0)

    # Missing skills count
    from backend.services.skill_gap_service import analyze_skill_gap
    gap_info = analyze_skill_gap(role_id, user_skills) if role_id else {"missing": []}
    missing_under_3 = len(gap_info.get("missing", [])) < 3

    # Projects in progress or completed
    proj_in_prog = execute_query(
        "SELECT count(*) as c FROM user_projects WHERE user_id = ? AND status IN ('in_progress', 'completed')",
        (user_id,),
        fetch_one=True
    )
    custom_proj_count = proj_in_prog["c"] if proj_in_prog else 0
    rec_proj_in_prog = execute_query(
        "SELECT count(*) as c FROM project_progress WHERE user_id = ? AND status IN ('in_progress', 'completed')",
        (user_id,),
        fetch_one=True
    )
    rec_proj_count = rec_proj_in_prog["c"] if rec_proj_in_prog else 0
    at_least_one_project = (custom_proj_count + rec_proj_count) > 0

    # 9-Item Completion Checklist (Section 6) with direct links
    resume_file_present = bool(profile and profile.get("resume_filename"))
    linkedin_present = bool(profile and profile.get("linkedin_link"))
    github_present = bool(profile and profile.get("github_link"))
    link_added = linkedin_present or github_present

    completion_checklist = [
        {"item": "Target role chosen", "done": bool(role_id), "link": "/pages/roles.html", "step": "Choose Role"},
        {"item": "Skills marked in Skill Gap", "done": len(user_skills) > 0, "link": "/pages/skill-gap.html", "step": "Skill Gap"},
        {"item": "Missing skills under 3", "done": missing_under_3, "link": "/pages/skill-gap.html", "step": "Skill Gap"},
        {"item": "Foundation stage started", "done": foundation_started, "link": "/pages/roadmap.html", "step": "Roadmap"},
        {"item": "At least 3 learning resources completed", "done": res_done_num >= 3, "link": "/pages/roadmap.html", "step": "Roadmap"},
        {"item": "At least 1 project in progress or completed", "done": at_least_one_project, "link": "/pages/projects.html", "step": "Projects"},
        {"item": "Mock interview completed", "done": len(mocks) >= 1, "link": "/pages/interview.html", "step": "Interview Prep"},
        {"item": "Resume uploaded", "done": resume_file_present, "link": "/pages/application-profile.html", "step": "Application Profile"},
        {"item": "LinkedIn or GitHub link added", "done": link_added, "link": "/pages/application-profile.html", "step": "Application Profile"}
    ]
    readiness["completion_checklist"] = completion_checklist
    readiness["profile_links"] = {
        "resume_uploaded": resume_file_present,
        "resume_filename": profile.get("resume_filename", "") if profile else "",
        "linkedin_added": linkedin_present,
        "github_added": github_present
    }

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
