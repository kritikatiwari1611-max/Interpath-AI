import pytest
from backend.services.skill_gap_service import analyze_skill_gap
from backend.services.roadmap_service import generate_roadmap

def test_empty_skills_gap():
    """Empty skills profile should report 0% match and list all role core requirements as missing."""
    res = analyze_skill_gap("python-developer", [])
    assert res["role_found"] is True
    assert res["overall_match_pct"] == 0.0
    assert len(res["missing"]) > 0
    assert "Python" in res["missing"]

def test_full_skills_match():
    """All required skills at Advanced level should yield 100% match."""
    skills = [
        {"skill_name": "Python", "level": "Advanced"},
        {"skill_name": "Data Structures", "level": "Advanced"},
        {"skill_name": "SQL", "level": "Advanced"},
        {"skill_name": "Flask", "level": "Advanced"},
        {"skill_name": "Git", "level": "Advanced"},
        {"skill_name": "REST APIs", "level": "Advanced"},
        {"skill_name": "Unit Testing", "level": "Advanced"}
    ]
    res = analyze_skill_gap("python-developer", skills)
    assert res["overall_match_pct"] == 100.0
    assert len(res["missing"]) == 0
    assert len(res["needs_improvement"]) == 0

def test_non_technical_role_no_programming():
    """Non-technical roles like Finance or Human Resources must not have programming requirements."""
    fin_res = analyze_skill_gap("finance", [])
    hr_res = analyze_skill_gap("human-resources", [])
    
    fin_reqs = [s["name"].lower() for s in fin_res["skills"]]
    hr_reqs = [s["name"].lower() for s in hr_res["skills"]]

    assert "python" not in fin_reqs
    assert "java" not in fin_reqs
    assert "html5" not in hr_reqs
    assert "javascript" not in hr_reqs

def test_roadmap_different_gaps_different_stages():
    """Two students with different gaps must get different roadmap tasks."""
    # Student A misses Python & SQL
    student_a_skills = [{"skill_name": "Git", "level": "Intermediate"}]
    # Student B has Python & SQL, but misses Flask & REST APIs
    student_b_skills = [
        {"skill_name": "Python", "level": "Advanced"},
        {"skill_name": "SQL", "level": "Intermediate"}
    ]

    roadmap_a = generate_roadmap("python-developer", student_a_skills)
    roadmap_b = generate_roadmap("python-developer", student_b_skills)

    tasks_a_titles = [t["title"] for st in roadmap_a["stages"] for t in st["tasks"]]
    tasks_b_titles = [t["title"] for st in roadmap_b["stages"] for t in st["tasks"]]

    assert tasks_a_titles != tasks_b_titles
    assert any("Python" in t for t in tasks_a_titles)
    # Student B already has Python Advanced, so Foundation task for Python should not be missing
    assert not any("Master Core Concepts of Python" in t for t in tasks_b_titles)
