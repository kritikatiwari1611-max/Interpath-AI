from flask import Blueprint, jsonify, session
from backend.db import execute_query
from backend.auth_utils import login_required

progress_bp = Blueprint("progress", __name__)

@progress_bp.route("/progress", methods=["GET"])
@login_required
def get_user_progress():
    user_id = session["user_id"]

    # 1. Skills improved (count of skills with Intermediate or Advanced level)
    skills = execute_query("SELECT level FROM user_skills WHERE user_id = ?", (user_id,), fetch_all=True)
    skills_improved = sum(1 for s in skills if s.get("level") in ("Intermediate", "Advanced"))
    total_skills = len(skills)

    # 2. Roadmap progress
    tasks = execute_query("SELECT status FROM roadmap_tasks WHERE user_id = ?", (user_id,), fetch_all=True)
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t["status"] == "completed")
    roadmap_pct = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0.0

    # 3. Resources completed
    resources = execute_query("SELECT completed FROM resource_progress WHERE user_id = ?", (user_id,), fetch_all=True)
    completed_resources = sum(1 for r in resources if r["completed"] == 1)

    # 4. Practice & Mock interviews
    attempts = execute_query("SELECT is_correct FROM interview_attempts WHERE user_id = ?", (user_id,), fetch_all=True)
    total_attempts = len(attempts)
    correct_attempts = sum(1 for a in attempts if a["is_correct"] == 1)
    practice_acc = round((correct_attempts / total_attempts * 100), 1) if total_attempts > 0 else 0.0

    mocks = execute_query("SELECT score, accuracy, created_at FROM mock_interviews WHERE user_id = ? ORDER BY created_at DESC", (user_id,), fetch_all=True)

    # 5. Projects completed
    projects = execute_query("SELECT status FROM user_projects WHERE user_id = ?", (user_id,), fetch_all=True)
    completed_projects = sum(1 for p in projects if p["status"] == "completed")

    # 6. Overall holistic progress score
    overall_progress = round(
        (min(100, skills_improved * 20) * 0.25) +
        (roadmap_pct * 0.30) +
        (min(100, completed_resources * 25) * 0.15) +
        (min(100, total_attempts * 10) * 0.15) +
        (min(100, completed_projects * 50) * 0.15)
    )

    return jsonify({
        "ok": True,
        "data": {
            "skills_improved": skills_improved,
            "total_skills": total_skills,
            "roadmap_pct": roadmap_pct,
            "completed_tasks": completed_tasks,
            "total_tasks": total_tasks,
            "resources_completed": completed_resources,
            "practice_attempted": total_attempts,
            "practice_accuracy": practice_acc,
            "mock_interviews_done": len(mocks),
            "projects_completed": completed_projects,
            "overall_progress": min(100, overall_progress),
            "recent_mocks": mocks[:3]
        }
    })
