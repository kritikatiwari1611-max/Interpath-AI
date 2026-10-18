import io
import pytest
from backend.app import create_app
from backend.db import init_db, execute_query
from backend.config import READINESS_APPLY_THRESHOLD, SKILL_LEVELS

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    init_db()

    with app.test_client() as client:
        # Create a test student account
        with client.session_transaction() as sess:
            # Clean db or insert test user
            execute_query("DELETE FROM users WHERE email = 'flow_test@example.com'", commit=True)
            uid = execute_query(
                "INSERT INTO users (email, name, password_hash, role) VALUES ('flow_test@example.com', 'Flow Student', 'dummy_hash', 'student')",
                commit=True
            )
            sess["user_id"] = uid
            sess["user_name"] = "Flow Student"
            sess["user_role"] = "student"
        yield client


def test_step1_role_selection(client):
    """Step 1: Choose Role saves selected_role_id in profile."""
    res = client.put("/api/profile/role", json={"role_id": "python-developer"})
    assert res.status_code == 200
    assert res.get_json()["ok"] is True

    # Verify via get profile
    prof_res = client.get("/api/profile")
    assert prof_res.status_code == 200
    assert prof_res.get_json()["data"]["profile"]["selected_role_id"] == "python-developer"


def test_step2_skill_gap_levels_and_saving(client):
    """Step 2: Interactive skill selection accepts Low (0.4), Medium (0.7), and High (1.0)."""
    assert SKILL_LEVELS["Low"] == 0.4
    assert SKILL_LEVELS["Medium"] == 0.7
    assert SKILL_LEVELS["High"] == 1.0

    client.put("/api/profile/role", json={"role_id": "python-developer"})

    # Save skills via PUT /api/skill-gap/skills
    skills_payload = [
        {"name": "Python", "level": "High"},
        {"name": "Flask", "level": "Medium"},
        {"name": "SQL", "level": "Low"}
    ]
    res = client.put("/api/skill-gap/skills", json={"skills": skills_payload})
    assert res.status_code == 200
    assert res.get_json()["ok"] is True

    # Check skill-gap analysis
    gap_res = client.get("/api/skill-gap")
    assert gap_res.status_code == 200
    gap_data = gap_res.get_json()["data"]
    assert "Python" in gap_data["learned"]
    assert "Flask" in gap_data["learned"]
    assert "SQL" in gap_data["needs_improvement"]


def test_step3_roadmap_segmented_status(client):
    """Step 3: Roadmap tasks and resources support 3-state segmented status."""
    client.put("/api/profile/role", json={"role_id": "python-developer"})
    res = client.get("/api/roadmap")
    assert res.status_code == 200
    roadmap_data = res.get_json()["data"]
    assert roadmap_data["role_selected"] is True

    # Update a task status to in_progress and completed
    first_task = roadmap_data["stages"][0]["tasks"][0]
    task_key = first_task["key"]

    t_res = client.put(f"/api/roadmap/tasks/{task_key}", json={"status": "in_progress", "role_id": "python-developer"})
    assert t_res.status_code == 200
    assert t_res.get_json()["data"]["status"] == "in_progress"

    # Update resource status
    r_res = client.put("/api/resources/res-py-1/status", json={"status": "completed"})
    assert r_res.status_code == 200
    assert r_res.get_json()["data"]["status"] == "completed"
    assert r_res.get_json()["data"]["completed"] is True


def test_step4_custom_project_validation_and_upload(client):
    """Step 4: Custom project form validates GitHub URL and handles PDF file upload."""
    # Invalid GitHub link should fail
    bad_res = client.post("/api/projects/custom", json={
        "title": "My Test Project",
        "description": "A great project built with Python",
        "github_link": "https://gitlab.com/user/repo"
    })
    assert bad_res.status_code == 400
    assert "github.com" in bad_res.get_json()["error"]

    # Valid project with mock PDF upload
    data = {
        "title": "Inventory Management System",
        "description": "Full stack project built with Flask and SQLite",
        "tech": "Python, Flask, SQLite",
        "github_link": "https://github.com/myuser/inventory-app",
        "demo_link": "https://inventory-demo.onrender.com",
        "status": "completed",
        "report_file": (io.BytesIO(b"%PDF-1.4 mock content"), "report.pdf")
    }
    good_res = client.post("/api/projects/custom", data=data, content_type="multipart/form-data")
    assert good_res.status_code == 201
    proj_id = good_res.get_json()["data"]["id"]

    # Verify custom projects list
    list_res = client.get("/api/projects/custom")
    assert list_res.status_code == 200
    custom_list = list_res.get_json()["data"]
    assert any(p["id"] == proj_id for p in custom_list)

    # Clean up project
    del_res = client.delete(f"/api/projects/custom/{proj_id}")
    assert del_res.status_code == 200


def test_step5_readiness_threshold_and_9item_checklist(client):
    """Step 5: Readiness returns threshold 65 and 9-item checklist."""
    assert READINESS_APPLY_THRESHOLD == 65

    res = client.get("/api/readiness")
    assert res.status_code == 200
    data = res.get_json()["data"]

    assert "is_ready_to_apply" in data
    assert "apply_threshold" in data
    assert data["apply_threshold"] == 65
    assert "completion_checklist" in data
    assert len(data["completion_checklist"]) == 9

    items = [c["item"] for c in data["completion_checklist"]]
    assert "Target role chosen" in items
    assert "Skills marked in Skill Gap" in items
    assert "Missing skills under 3" in items
    assert "Foundation stage started" in items
    assert "At least 3 learning resources completed" in items
    assert "At least 1 project in progress or completed" in items
    assert "Mock interview completed" in items
    assert "Resume uploaded" in items
    assert "LinkedIn or GitHub link added" in items


def test_step6_application_profile_and_resume(client):
    """Step 6: Resume upload/download/delete and profile URL validations."""
    # 1. Invalid LinkedIn link should fail
    bad_li = client.put("/api/profile", json={"linkedin_link": "https://twitter.com/user"})
    assert bad_li.status_code == 400

    # 2. Upload valid resume PDF
    resume_data = {
        "resume": (io.BytesIO(b"%PDF-1.5 student resume content"), "my_resume.pdf")
    }
    up_res = client.post("/api/profile/resume-upload", data=resume_data, content_type="multipart/form-data")
    assert up_res.status_code == 200
    saved_filename = up_res.get_json()["data"]["filename"]

    # 3. Download the uploaded resume
    dl_res = client.get(f"/api/uploads/{saved_filename}")
    assert dl_res.status_code == 200
    assert dl_res.data == b"%PDF-1.5 student resume content"

    # 4. Valid links update
    links_res = client.put("/api/profile", json={
        "linkedin_link": "https://www.linkedin.com/in/student-dev",
        "github_link": "https://github.com/student-dev"
    })
    assert links_res.status_code == 200

    # 5. Internships endpoint reflects application readiness
    int_res = client.get("/api/internships")
    assert int_res.status_code == 200
    app_ready = int_res.get_json()["data"]["application_readiness"]
    assert app_ready["resume_uploaded"] is True
    assert app_ready["linkedin_added"] is True
    assert app_ready["github_added"] is True
    assert app_ready["all_ready"] is True

    # 6. Delete resume
    del_res = client.post("/api/profile/resume-delete")
    assert del_res.status_code == 200
