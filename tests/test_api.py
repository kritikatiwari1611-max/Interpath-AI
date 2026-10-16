import pytest
import json
from backend.app import create_app
from backend.db import init_db
from database.seed import seed_database

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    init_db()
    seed_database()
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert data["status"] == "healthy"

def test_auth_and_user_isolation(client):
    # Log in as Student A (BCA)
    res_a = client.post("/api/auth/login", json={"email": "student@demo.com", "password": "Student@123"})
    assert res_a.status_code == 200

    # Read Student A profile
    prof_a = client.get("/api/profile").get_json()["data"]
    assert prof_a["profile"]["course"] == "BCA"

    # Logout
    client.post("/api/auth/logout")

    # Log in as Student B (Priya, B.Com)
    res_b = client.post("/api/auth/login", json={"email": "priya@demo.com", "password": "Student@123"})
    assert res_b.status_code == 200

    prof_b = client.get("/api/profile").get_json()["data"]
    assert prof_b["profile"]["course"] == "B.Com"
    # Ensure Student B cannot see Student A's skills
    skill_names = [s["skill_name"] for s in prof_b["skills"]]
    assert "Flask" not in skill_names
    assert "Financial Modeling" in skill_names

def test_admin_access_control(client):
    # Log in as student
    client.post("/api/auth/login", json={"email": "student@demo.com", "password": "Student@123"})
    # Attempting to access admin stats must return 403 Forbidden
    res = client.get("/api/admin/stats")
    assert res.status_code == 403

    client.post("/api/auth/logout")

    # Log in as admin
    client.post("/api/auth/login", json={"email": "admin@demo.com", "password": "Admin@123"})
    res_admin = client.get("/api/admin/stats")
    assert res_admin.status_code == 200
    assert res_admin.get_json()["ok"] is True

def test_roadmap_task_status_flow(client):
    client.post("/api/auth/login", json={"email": "student@demo.com", "password": "Student@123"})
    
    # Update task status
    res = client.put("/api/roadmap/tasks/st1_test_task", json={"status": "completed", "role_id": "python-developer"})
    assert res.status_code == 200
    assert res.get_json()["data"]["status"] == "completed"
