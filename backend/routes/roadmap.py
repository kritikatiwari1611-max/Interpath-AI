import json
from flask import Blueprint, request, jsonify, session
from backend.db import execute_query
from backend.auth_utils import login_required
from backend.services.roadmap_service import (
    generate_roadmap,
    generate_study_plan,
    get_skill_explanations,
    get_all_resources
)
from backend.services import ai_service

roadmap_bp = Blueprint("roadmap", __name__)

@roadmap_bp.route("/roadmap", methods=["GET"])
@login_required
def get_roadmap():
    """Returns the deterministic 4-stage personalized roadmap."""
    user_id = session["user_id"]
    profile = execute_query("SELECT selected_role_id FROM student_profiles WHERE user_id = ?", (user_id,), fetch_one=True)
    role_id = profile.get("selected_role_id") if profile else None

    if not role_id:
        role_id = "python-developer"
        if profile:
            execute_query("UPDATE student_profiles SET selected_role_id = ? WHERE user_id = ?", (role_id, user_id), commit=True)
        else:
            execute_query("INSERT INTO student_profiles (user_id, selected_role_id) VALUES (?, ?)", (user_id, role_id), commit=True)

    user_skills = execute_query("SELECT skill_name, level FROM user_skills WHERE user_id = ?", (user_id,), fetch_all=True)
    
    # Load user's saved task status records
    task_rows = execute_query(
        "SELECT task_key, status FROM roadmap_tasks WHERE user_id = ? AND role_id = ?",
        (user_id, role_id),
        fetch_all=True
    )
    user_tasks_status = {r["task_key"]: r["status"] for r in task_rows}

    roadmap_data = generate_roadmap(role_id, user_skills, user_tasks_status)
    roadmap_data["role_selected"] = True

    return jsonify({"ok": True, "data": roadmap_data})


@roadmap_bp.route("/roadmap/tasks/<task_key>", methods=["PUT"])
@login_required
def update_task_status(task_key):
    """Updates the status of a specific roadmap task (pending / in_progress / completed)."""
    user_id = session["user_id"]
    data = request.get_json() or {}
    status = data.get("status", "pending")
    role_id = data.get("role_id", "")

    if not role_id:
        profile = execute_query("SELECT selected_role_id FROM student_profiles WHERE user_id = ?", (user_id,), fetch_one=True)
        role_id = profile.get("selected_role_id", "python-developer") if profile else "python-developer"

    existing = execute_query(
        "SELECT id FROM roadmap_tasks WHERE user_id = ? AND role_id = ? AND task_key = ?",
        (user_id, role_id, task_key),
        fetch_one=True
    )
    if existing:
        execute_query(
            "UPDATE roadmap_tasks SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, existing["id"]),
            commit=True
        )
    else:
        execute_query(
            "INSERT INTO roadmap_tasks (user_id, role_id, task_key, status) VALUES (?, ?, ?, ?)",
            (user_id, role_id, task_key, status),
            commit=True
        )

    return jsonify({"ok": True, "data": {"task_key": task_key, "status": status}})


# -----------------------------------------------------------------------------
# WEEKLY STUDY PLAN & SKILL EXPLANATION ROUTES (Section 9)
# -----------------------------------------------------------------------------

@roadmap_bp.route("/roadmap/skill-explanations", methods=["GET"])
@login_required
def get_explanations():
    """Returns 'why this skill matters' explanations for the student's current gaps."""
    user_id = session["user_id"]
    profile = execute_query("SELECT selected_role_id FROM student_profiles WHERE user_id = ?", (user_id,), fetch_one=True)
    role_id = profile.get("selected_role_id", "python-developer") if profile else "python-developer"
    user_skills = execute_query("SELECT skill_name, level FROM user_skills WHERE user_id = ?", (user_id,), fetch_all=True)

    explanations = get_skill_explanations(role_id, user_skills)
    return jsonify({"ok": True, "data": explanations})


@roadmap_bp.route("/roadmap/plan", methods=["GET"])
@login_required
def get_study_plan():
    """
    Returns the saved study plan for the current student and selected role,
    with attached session completion statuses, week progress bars, and skills_changed banner check.
    """
    user_id = session["user_id"]
    profile = execute_query("SELECT selected_role_id FROM student_profiles WHERE user_id = ?", (user_id,), fetch_one=True)
    role_id = profile.get("selected_role_id", "python-developer") if profile else "python-developer"

    # Fetch latest saved study plan for this user and role
    plan_row = execute_query(
        "SELECT id, role_id, mode, inputs_json, plan_json, created_at FROM study_plans WHERE user_id = ? AND role_id = ? ORDER BY id DESC LIMIT 1",
        (user_id, role_id),
        fetch_one=True
    )
    if not plan_row:
        return jsonify({"ok": True, "data": None})

    try:
        plan_data = json.loads(plan_row["plan_json"])
        inputs_data = json.loads(plan_row["inputs_json"])
    except Exception:
        return jsonify({"ok": True, "data": None})

    plan_id = plan_row["id"]

    # Load session statuses for this plan
    session_rows = execute_query(
        "SELECT session_key, status FROM plan_sessions WHERE user_id = ? AND plan_id = ?",
        (user_id, plan_id),
        fetch_all=True
    )
    status_map = {r["session_key"]: r["status"] for r in (session_rows or [])}

    # Attach statuses and compute weekly progress
    total_sessions_count = 0
    completed_sessions_count = 0
    current_week_detected = None

    for w in plan_data.get("weeks", []):
        w_total = len(w.get("sessions", []))
        w_done = 0
        all_res_map = {r["id"]: r for r in get_all_resources()}
        for s in w.get("sessions", []):
            s_key = s.get("session_key", "")
            s_status = status_map.get(s_key, "pending")
            s["status"] = s_status
            s["resources"] = [all_res_map[rid] for rid in s.get("resource_ids", []) if rid in all_res_map]
            total_sessions_count += 1
            if s_status == "completed":
                w_done += 1
                completed_sessions_count += 1

        w["total_sessions"] = w_total
        w["completed_sessions"] = w_done
        w["progress_pct"] = round((w_done / w_total * 100), 1) if w_total > 0 else 0.0

        if current_week_detected is None and w["progress_pct"] < 100.0:
            current_week_detected = w.get("week", 1)

    overall_progress_pct = round((completed_sessions_count / total_sessions_count * 100), 1) if total_sessions_count > 0 else 0.0

    # Check if student's skills changed since the plan was created
    current_skills = execute_query("SELECT skill_name, level FROM user_skills WHERE user_id = ?", (user_id,), fetch_all=True)
    saved_skills = inputs_data.get("skills", [])
    
    # Compare skills sets
    current_skills_dict = {s["skill_name"]: s["level"] for s in (current_skills or [])}
    saved_skills_dict = {s["name"]: s["level"] for s in (saved_skills or [])}
    skills_changed = (current_skills_dict != saved_skills_dict)

    plan_data["plan_id"] = plan_id
    plan_data["overall_progress_pct"] = overall_progress_pct
    plan_data["completed_sessions_count"] = completed_sessions_count
    plan_data["total_sessions_count"] = total_sessions_count
    plan_data["current_week"] = current_week_detected or 1
    plan_data["skills_changed"] = skills_changed
    plan_data["inputs"] = inputs_data

    return jsonify({"ok": True, "data": plan_data})


@roadmap_bp.route("/roadmap/plan", methods=["POST"])
@login_required
def create_study_plan():
    """
    Generates and saves a new personalized weekly study plan.
    Carries over completed session work from previous plan instances.
    """
    user_id = session["user_id"]
    data = request.get_json() or {}

    profile = execute_query(
        "SELECT course, specialization, semester, selected_role_id FROM student_profiles WHERE user_id = ?",
        (user_id,),
        fetch_one=True
    )
    role_id = profile.get("selected_role_id", "python-developer") if profile else "python-developer"
    user_skills = execute_query("SELECT skill_name, level FROM user_skills WHERE user_id = ?", (user_id,), fetch_all=True)

    hours_per_week = data.get("hours_per_week", 10)
    weeks = data.get("weeks", 6)
    learning_style = data.get("learning_style", "Videos first")
    ready_by = data.get("ready_by", "")

    student_context = {
        "role_id": role_id,
        "course": profile.get("course", "BCA") if profile else "BCA",
        "specialization": profile.get("specialization", "") if profile else "",
        "semester": profile.get("semester", "") if profile else "",
        "skills": [{"name": s["skill_name"], "level": s["level"]} for s in (user_skills or [])],
        "hours_per_week": hours_per_week,
        "weeks": weeks,
        "learning_style": learning_style,
        "ready_by": ready_by,
        "preferred_language": "en"
    }

    # Determine mode: check if OpenAI API is configured, quota available, and regeneration limit
    can_use_ai, _ = ai_service.is_ai_available(user_id)
    if can_use_ai:
        can_regen = ai_service.check_and_increment_regen_quota(user_id)
        if can_regen:
            ai_allowed = ai_service.check_and_increment_quota(user_id)
            mode = "openai" if ai_allowed else "demo"
        else:
            mode = "demo"
    else:
        mode = "demo"

    # Generate plan via unified roadmap service
    plan_data = generate_study_plan(student_context, mode=mode)

    # Carry-over logic: look for previous plan sessions to preserve completed work
    previous_plan = execute_query(
        "SELECT id FROM study_plans WHERE user_id = ? AND role_id = ? ORDER BY id DESC LIMIT 1",
        (user_id, role_id),
        fetch_one=True
    )
    carryover_status_map = {}
    if previous_plan:
        prev_sessions = execute_query(
            "SELECT session_key, status FROM plan_sessions WHERE user_id = ? AND plan_id = ?",
            (user_id, previous_plan["id"]),
            fetch_all=True
        )
        for ps in (prev_sessions or []):
            if ps["status"] in ["completed", "in_progress"]:
                carryover_status_map[ps["session_key"]] = ps["status"]

    # Save new plan into study_plans table
    plan_id = execute_query(
        """INSERT INTO study_plans (user_id, role_id, mode, inputs_json, plan_json) 
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, role_id, plan_data["mode"], json.dumps(student_context), json.dumps(plan_data)),
        commit=True
    )

    # Insert plan sessions with carried-over statuses
    total_sessions_count = 0
    completed_sessions_count = 0

    for w in plan_data.get("weeks", []):
        w_done = 0
        w_total = len(w.get("sessions", []))
        for s in w.get("sessions", []):
            s_key = s.get("session_key", "")
            
            # Carry over status if previously completed/in_progress
            s_status = carryover_status_map.get(s_key, "pending")
            # Also check if same skill + task_type was completed
            if s_status == "pending":
                for prev_k, prev_st in carryover_status_map.items():
                    if s.get("skill", "").lower() in prev_k and s.get("task_type", "") in prev_k:
                        s_status = prev_st
                        break

            all_res_map = {r["id"]: r for r in get_all_resources()}
            s["resources"] = [all_res_map[rid] for rid in s.get("resource_ids", []) if rid in all_res_map]
            s["status"] = s_status
            total_sessions_count += 1
            if s_status == "completed":
                w_done += 1
                completed_sessions_count += 1

            execute_query(
                """INSERT INTO plan_sessions (user_id, plan_id, session_key, status) 
                   VALUES (?, ?, ?, ?)""",
                (user_id, plan_id, s_key, s_status),
                commit=True
            )

        w["total_sessions"] = w_total
        w["completed_sessions"] = w_done
        w["progress_pct"] = round((w_done / w_total * 100), 1) if w_total > 0 else 0.0

    plan_data["plan_id"] = plan_id
    plan_data["overall_progress_pct"] = round((completed_sessions_count / total_sessions_count * 100), 1) if total_sessions_count > 0 else 0.0
    plan_data["completed_sessions_count"] = completed_sessions_count
    plan_data["total_sessions_count"] = total_sessions_count
    plan_data["current_week"] = 1
    plan_data["skills_changed"] = False
    plan_data["inputs"] = student_context

    return jsonify({"ok": True, "data": plan_data})


@roadmap_bp.route("/roadmap/plan/sessions/<session_key>", methods=["PUT"])
@login_required
def update_plan_session_status(session_key):
    """Saves session status: Pending / In Progress / Completed."""
    user_id = session["user_id"]
    data = request.get_json() or {}
    status = data.get("status", "pending")
    if status not in ["pending", "in_progress", "completed"]:
        status = "pending"

    profile = execute_query("SELECT selected_role_id FROM student_profiles WHERE user_id = ?", (user_id,), fetch_one=True)
    role_id = profile.get("selected_role_id", "python-developer") if profile else "python-developer"

    plan = execute_query(
        "SELECT id FROM study_plans WHERE user_id = ? AND role_id = ? ORDER BY id DESC LIMIT 1",
        (user_id, role_id),
        fetch_one=True
    )
    if not plan:
        return jsonify({"ok": False, "error": "No active study plan found"}), 404

    plan_id = plan["id"]

    existing = execute_query(
        "SELECT id FROM plan_sessions WHERE user_id = ? AND plan_id = ? AND session_key = ?",
        (user_id, plan_id, session_key),
        fetch_one=True
    )
    if existing:
        execute_query(
            "UPDATE plan_sessions SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, existing["id"]),
            commit=True
        )
    else:
        execute_query(
            "INSERT INTO plan_sessions (user_id, plan_id, session_key, status) VALUES (?, ?, ?, ?)",
            (user_id, plan_id, session_key, status),
            commit=True
        )

    return jsonify({"ok": True, "data": {"session_key": session_key, "status": status}})
