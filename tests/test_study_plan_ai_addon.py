import json
from datetime import date
import pytest
from backend.app import create_app
from backend.db import init_db, execute_query
from backend.services.roadmap_service import (
    generate_study_plan,
    get_skill_explanations,
    build_rule_based_study_plan,
    load_resources_map
)
from backend.services import ai_service


@pytest.fixture
def test_client():
    app = create_app()
    app.config["TESTING"] = True
    init_db()

    with app.test_client() as client:
        with client.session_transaction() as sess:
            execute_query("DELETE FROM users WHERE email = 'student_plan@example.com'", commit=True)
            uid = execute_query(
                "INSERT INTO users (email, name, password_hash, role) VALUES ('student_plan@example.com', 'Plan Student', 'hash', 'student')",
                commit=True
            )
            sess["user_id"] = uid
            sess["user_name"] = "Plan Student"
            sess["user_role"] = "student"
        yield client, uid


# 1. UNKNOWN RESOURCE IDS REMOVED
def test_unknown_resource_ids_removed(monkeypatch):
    """When the AI invents fake resource IDs (e.g. 'r_fake_999'), the server drops them."""
    resources_map = load_resources_map()
    real_id = next(iter(resources_map.keys()))

    fake_ai_plan = {
        "overview": "Focus on SQL and Python basics.",
        "skill_explanations": [],
        "weeks": [
            {
                "week": 1,
                "theme": "Database Essentials",
                "goal": "Master SQL basics",
                "skills": ["SQL"],
                "sessions": [
                    {
                        "title": "SQL Query Syntax",
                        "minutes": 45,
                        "resource_ids": [real_id, "r_invented_999", "http://fake-link.com"],
                        "task_type": "learn",
                        "skill": "SQL"
                    }
                ],
                "checkpoint": "Write a SELECT query",
                "tip": "Practice indexing."
            }
        ],
        "revision_tips": ["Review joins weekly."],
        "confidence_note": "Solid plan."
    }
    monkeypatch.setattr(ai_service, "call_ai_study_plan", lambda ctx: fake_ai_plan)

    context = {
        "user_id": 999,
        "role_id": "backend-developer",
        "role_title": "Backend Developer",
        "hours_per_week": 10,
        "weeks": 4,
        "learning_style": "Videos first",
        "skills": [{"name": "SQL", "level": "LOW"}, {"name": "Python", "level": "LOW"}],
        "missing_skills": ["SQL", "Python"],
        "weak_skills": []
    }

    plan = generate_study_plan(context, mode="openai")
    session = plan["weeks"][0]["sessions"][0]

    # Check that invented resource ID was stripped
    assert "r_invented_999" not in session["resource_ids"]
    assert "http://fake-link.com" not in session["resource_ids"]
    assert real_id in session["resource_ids"]


# 2. MEDIUM AND HIGH SKILLS EXCLUDED FROM NEW LEARNING
def test_medium_and_high_skills_excluded(monkeypatch):
    """Skills already marked MEDIUM or HIGH should not appear in new learning sessions."""
    fake_ai_plan = {
        "overview": "Learn Docker and SQL.",
        "skill_explanations": [],
        "weeks": [
            {
                "week": 1,
                "theme": "Advanced Skills",
                "goal": "Learn Docker and SQL",
                "skills": ["Docker", "SQL"],
                "sessions": [
                    {"title": "Docker Setup", "minutes": 45, "resource_ids": [], "task_type": "learn", "skill": "Docker"},
                    {"title": "SQL Basics", "minutes": 45, "resource_ids": [], "task_type": "learn", "skill": "SQL"}
                ],
                "checkpoint": "Mini task",
                "tip": "Tip"
            }
        ],
        "revision_tips": [],
        "confidence_note": ""
    }
    monkeypatch.setattr(ai_service, "call_ai_study_plan", lambda ctx: fake_ai_plan)

    context = {
        "user_id": 999,
        "role_id": "backend-developer",
        "role_title": "Backend Developer",
        "hours_per_week": 10,
        "weeks": 4,
        "learning_style": "Videos first",
        "skills": [{"name": "Docker", "level": "HIGH"}, {"name": "SQL", "level": "LOW"}],
        "missing_skills": ["SQL"],
        "weak_skills": []
    }

    plan = generate_study_plan(context, mode="openai")
    # All sessions should be SQL, Docker shouldn't be added as new learning
    session_skills = [s["skill"] for s in plan["weeks"][0]["sessions"]]
    assert "Docker" not in session_skills
    assert "SQL" in session_skills


# 3. ALL MISSING OR LOW CORE SKILLS APPEAR
def test_all_missing_core_skills_appear(monkeypatch):
    """If the AI omits a Missing or LOW core skill, the server appends it to a week."""
    fake_ai_plan = {
        "overview": "Focus only on Git.",
        "skill_explanations": [],
        "weeks": [
            {
                "week": 1,
                "theme": "Version Control",
                "goal": "Git basics",
                "skills": ["Git"],
                "sessions": [
                    {"title": "Git Commit", "minutes": 45, "resource_ids": [], "task_type": "learn", "skill": "Git"}
                ],
                "checkpoint": "Make a commit",
                "tip": "Tip"
            }
        ],
        "revision_tips": [],
        "confidence_note": ""
    }
    monkeypatch.setattr(ai_service, "call_ai_study_plan", lambda ctx: fake_ai_plan)

    context = {
        "user_id": 999,
        "role_id": "backend-developer",
        "role_title": "Backend Developer",
        "hours_per_week": 15,
        "weeks": 4,
        "learning_style": "Videos first",
        "skills": [{"name": "Git", "level": "LOW"}, {"name": "Python", "level": "LOW"}],
        "missing_skills": ["Git", "Python"],
        "weak_skills": []
    }

    plan = generate_study_plan(context, mode="openai")
    all_plan_skills = set()
    for w in plan["weeks"]:
        for s in w["sessions"]:
            all_plan_skills.add(s["skill"])

    # Both Git and Python must appear in the final plan
    assert "Git" in all_plan_skills
    assert "Python" in all_plan_skills


# 4. WEEKLY MINUTES TRIMMED TO FIT HOURS LIMIT
def test_weekly_minutes_trimmed_to_limit(monkeypatch):
    """Server enforces week_minutes <= hours_per_week * 60 by trimming excess sessions."""
    fake_ai_plan = {
        "overview": "Overloaded week.",
        "skill_explanations": [],
        "weeks": [
            {
                "week": 1,
                "theme": "Heavy Week",
                "goal": "Too many tasks",
                "skills": ["SQL"],
                "sessions": [
                    {"title": "Task 1", "minutes": 120, "resource_ids": [], "task_type": "learn", "skill": "SQL"},
                    {"title": "Task 2", "minutes": 120, "resource_ids": [], "task_type": "practice", "skill": "SQL"},
                    {"title": "Task 3", "minutes": 120, "resource_ids": [], "task_type": "practice", "skill": "SQL"}  # Total 360 > 300
                ],
                "checkpoint": "Check",
                "tip": "Tip"
            }
        ],
        "revision_tips": [],
        "confidence_note": ""
    }
    monkeypatch.setattr(ai_service, "call_ai_study_plan", lambda ctx: fake_ai_plan)

    # 5 hours/week = max 300 minutes
    context = {
        "user_id": 999,
        "role_id": "backend-developer",
        "role_title": "Backend Developer",
        "hours_per_week": 5,
        "weeks": 4,
        "learning_style": "Videos first",
        "skills": [
            {"name": "SQL", "level": "LOW"},
            {"name": "Python", "level": "HIGH"},
            {"name": "REST APIs", "level": "HIGH"}
        ],
        "missing_skills": ["SQL"],
        "weak_skills": []
    }

    plan = generate_study_plan(context, mode="openai")
    week1 = plan["weeks"][0]
    assert week1["total_minutes"] <= 300
    assert len(week1["sessions"]) == 2  # Task 3 was trimmed


# 5. BAD JSON OR ERROR FALLS BACK TO RULE-BASED PLAN
def test_bad_json_falls_back_to_rule_based(monkeypatch):
    """When the AI returns None or invalid JSON, server gracefully falls back to rule-based plan."""
    monkeypatch.setattr(ai_service, "call_ai_study_plan", lambda ctx: None)

    context = {
        "user_id": 999,
        "role_id": "backend-developer",
        "role_title": "Backend Developer",
        "hours_per_week": 10,
        "weeks": 6,
        "learning_style": "Practice first",
        "skills": [{"name": "Python", "level": "LOW"}, {"name": "SQL", "level": "LOW"}],
        "missing_skills": ["Python", "SQL"],
        "weak_skills": []
    }

    plan = generate_study_plan(context, mode="openai")
    assert plan["mode"] == "demo"
    assert "Rule-based" in plan["confidence_note"] or "rule-based" in plan["confidence_note"].lower()
    assert len(plan["weeks"]) == 6
    assert plan["weeks"][0]["total_minutes"] > 0


# 6. NON-TECHNICAL ROLES GET NO PROGRAMMING SESSIONS
def test_non_technical_role_no_programming():
    """Finance, HR, and Marketing roles must not have programming skills assigned."""
    context = {
        "user_id": 999,
        "role_id": "human-resources",
        "role_title": "HR Specialist",
        "hours_per_week": 10,
        "weeks": 4,
        "learning_style": "Videos first",
        "skills": [{"name": "Recruitment", "level": "LOW"}],
        "missing_skills": ["Recruitment"],
        "weak_skills": []
    }

    plan = build_rule_based_study_plan(context)
    forbidden_tokens = ["python", "c++", "java", "coding", "algorithm", "javascript"]

    for w in plan["weeks"]:
        for s in w["sessions"]:
            title_lower = s["title"].lower()
            for tok in forbidden_tokens:
                assert tok not in title_lower, f"Forbidden technical token '{tok}' found in non-tech role session: {s['title']}"


# 7. DIFFERENT SKILL INPUTS PRODUCE DIFFERENT PLANS
def test_different_skills_produce_different_plans():
    """A student with Excel gap gets Excel; one with SQL gap gets SQL first."""
    context_excel = {
        "user_id": 1,
        "role_id": "data-analyst",
        "role_title": "Data Analyst",
        "hours_per_week": 10,
        "weeks": 4,
        "learning_style": "Videos first",
        "skills": [{"name": "SQL", "level": "HIGH"}, {"name": "Excel & Advanced Formulas", "level": "LOW"}],
        "missing_skills": ["Excel & Advanced Formulas"],
        "weak_skills": []
    }

    context_sql = {
        "user_id": 2,
        "role_id": "data-analyst",
        "role_title": "Data Analyst",
        "hours_per_week": 10,
        "weeks": 4,
        "learning_style": "Videos first",
        "skills": [{"name": "Excel & Advanced Formulas", "level": "HIGH"}, {"name": "SQL", "level": "LOW"}],
        "missing_skills": ["SQL"],
        "weak_skills": []
    }

    plan_excel = build_rule_based_study_plan(context_excel)
    plan_sql = build_rule_based_study_plan(context_sql)

    assert plan_excel["weeks"][0]["skills"] != plan_sql["weeks"][0]["skills"]
    assert "Excel & Advanced Formulas" in plan_excel["weeks"][0]["skills"]
    assert "SQL" in plan_sql["weeks"][0]["skills"]


# 8. DEMO MODE WORKS WITHOUT API KEY
def test_demo_mode_without_api_key():
    """Demo mode must execute fully and return valid weeks and sessions without an API key."""
    context = {
        "user_id": 999,
        "role_id": "frontend-developer",
        "role_title": "Frontend Developer",
        "hours_per_week": 10,
        "weeks": 8,
        "learning_style": "Videos first",
        "skills": [{"name": "React", "level": "LOW"}, {"name": "JavaScript", "level": "LOW"}],
        "missing_skills": ["React", "JavaScript"],
        "weak_skills": []
    }

    plan = generate_study_plan(context, mode="demo")
    assert plan["mode"] == "demo"
    assert len(plan["weeks"]) == 8
    assert len(plan["weeks"][0]["sessions"]) > 0


# 9. DAILY PLAN REGENERATION LIMIT FALLBACK
def test_regeneration_limit_fallback():
    """When a user reaches the daily regeneration quota (5), check_and_increment_regen_quota fails."""
    user_id = 999
    today = date.today().isoformat()
    ai_service._DAILY_REGEN_USAGE[(user_id, today)] = 5

    allowed = ai_service.check_and_increment_regen_quota(user_id)
    assert allowed is False


# 10. REGENERATING CARRIES OVER COMPLETED WORK
def test_regenerating_carries_over_completed_work(test_client):
    """When regenerating a study plan, sessions completed in the prior plan remain completed."""
    client, user_id = test_client

    # Set student profile
    execute_query(
        "INSERT INTO student_profiles (user_id, selected_role_id, course) VALUES (?, ?, ?)",
        (user_id, "backend-developer", "BCA"),
        commit=True
    )
    execute_query("INSERT INTO user_skills (user_id, skill_name, level) VALUES (?, ?, ?)", (user_id, "Python", "LOW"), commit=True)
    execute_query("INSERT INTO user_skills (user_id, skill_name, level) VALUES (?, ?, ?)", (user_id, "SQL", "LOW"), commit=True)

    # Generate initial plan via POST
    res1 = client.post("/api/roadmap/plan", json={
        "hours_per_week": 10,
        "weeks": 4,
        "learning_style": "Videos first"
    })
    assert res1.status_code == 200
    plan1 = res1.get_json()["data"]
    first_session_key = plan1["weeks"][0]["sessions"][0]["session_key"]

    # Mark the first session as completed via PUT
    put_res = client.put(f"/api/roadmap/plan/sessions/{first_session_key}", json={
        "status": "completed"
    })
    assert put_res.status_code == 200

    # Regenerate the plan
    res2 = client.post("/api/roadmap/plan", json={
        "hours_per_week": 10,
        "weeks": 4,
        "learning_style": "Videos first"
    })
    assert res2.status_code == 200

    # Check GET /api/roadmap/plan - the completed session status must carry over
    get_res = client.get("/api/roadmap/plan")
    assert get_res.status_code == 200
    plan2 = get_res.get_json()["data"]
    assert plan2["weeks"][0]["sessions"][0]["status"] == "completed"


# 11. STUDENT ISOLATION
def test_student_isolation(test_client):
    """Student B cannot view or modify Student A's study plan or session progress."""
    client, uid_a = test_client

    execute_query("DELETE FROM users WHERE email = 'student_b_iso@example.com'", commit=True)
    # Create Student B
    uid_b = execute_query(
        "INSERT INTO users (email, name, password_hash, role) VALUES ('student_b_iso@example.com', 'Student B', 'hash', 'student')",
        commit=True
    )

    # Student A creates a profile and generates a plan
    execute_query(
        "INSERT INTO student_profiles (user_id, selected_role_id, course) VALUES (?, ?, ?)",
        (uid_a, "backend-developer", "BCA"),
        commit=True
    )
    client.post("/api/roadmap/plan", json={"hours_per_week": 10, "weeks": 4})

    # Switch session to Student B
    with client.session_transaction() as sess:
        sess["user_id"] = uid_b

    # Student B should have no active plan
    res = client.get("/api/roadmap/plan")
    assert res.status_code == 200
    assert res.get_json()["data"] is None


# 12. READINESS SCORE UNCHANGED BY PLAN GENERATION
def test_readiness_score_unchanged_by_plan(test_client):
    """Generating or updating an AI study plan never alters the student's readiness score."""
    client, user_id = test_client

    execute_query(
        "INSERT INTO student_profiles (user_id, selected_role_id, course) VALUES (?, ?, ?)",
        (user_id, "backend-developer", "BCA"),
        commit=True
    )
    execute_query("INSERT INTO user_skills (user_id, skill_name, level) VALUES (?, ?, ?)", (user_id, "SQL", "LOW"), commit=True)
    execute_query("INSERT INTO user_skills (user_id, skill_name, level) VALUES (?, ?, ?)", (user_id, "Python", "MEDIUM"), commit=True)

    # Get readiness score before
    r1 = client.get("/api/readiness")
    score_before = r1.get_json()["data"]["overall"]

    # Generate plan
    client.post("/api/roadmap/plan", json={"hours_per_week": 10, "weeks": 4})

    # Get readiness score after
    r2 = client.get("/api/readiness")
    score_after = r2.get_json()["data"]["overall"]

    assert score_before == score_after
