import pytest
from backend.services.readiness_service import calculate_readiness_score, get_weights
from backend.services.role_helper import get_role_by_id

def test_empty_profile_provisional():
    """Empty skills and projects must yield Provisional status."""
    role = get_role_by_id("python-developer")
    res = calculate_readiness_score(
        role_id="python-developer",
        user_skills=[],
        user_projects=[],
        resume_checklist={},
        interview_stats={},
        user_certifications=[],
        role_meta=role
    )
    assert res["provisional"] is True
    assert len(res["reasons"]) > 0
    assert "Profile is incomplete" in res["reasons"][0]

def test_irrelevant_project_no_credit():
    """Projects that do not match project keywords or role skills give 0 project points."""
    role = get_role_by_id("python-developer")
    irrelevant_project = [{
        "title": "Bakery Inventory System",
        "description": "Cookbook recipe index",
        "tech": "PHP, MySQL",
        "status": "completed"
    }]
    res = calculate_readiness_score(
        role_id="python-developer",
        user_skills=[{"skill_name": "Python", "level": "Beginner"}],
        user_projects=irrelevant_project,
        resume_checklist={},
        interview_stats={},
        user_certifications=[],
        role_meta=role
    )
    assert res["category_scores"]["projects"] == 0.0

def test_relevant_project_raises_score():
    """Relevant completed project matching role keywords awards points."""
    role = get_role_by_id("python-developer")
    relevant_project = [{
        "title": "Student Attendance REST API",
        "description": "Python Flask backend API with token auth",
        "tech": "Python, Flask, SQLite",
        "status": "completed"
    }]
    res = calculate_readiness_score(
        role_id="python-developer",
        user_skills=[{"skill_name": "Python", "level": "Intermediate"}],
        user_projects=relevant_project,
        resume_checklist={},
        interview_stats={},
        user_certifications=[],
        role_meta=role
    )
    assert res["category_scores"]["projects"] > 0
    assert res["matched_projects_count"] == 1

def test_certifications_only_matching():
    """Only certifications that match role keywords earn credit."""
    role = get_role_by_id("finance")
    unrelated_cert = [{"title": "AWS Certified Solutions Architect", "issuer": "Amazon"}]
    matching_cert = [{"title": "Corporate Finance Institute Financial Modeling Certification", "issuer": "CFI"}]

    res_unrelated = calculate_readiness_score(
        role_id="finance",
        user_skills=[{"skill_name": "Financial Modeling", "level": "Intermediate"}],
        user_projects=[],
        resume_checklist={},
        interview_stats={},
        user_certifications=unrelated_cert,
        role_meta=role
    )
    assert res_unrelated["category_scores"]["certifications"] == 0.0

    res_matching = calculate_readiness_score(
        role_id="finance",
        user_skills=[{"skill_name": "Financial Modeling", "level": "Intermediate"}],
        user_projects=[],
        resume_checklist={},
        interview_stats={},
        user_certifications=matching_cert,
        role_meta=role
    )
    assert res_matching["category_scores"]["certifications"] > 0.0

def test_role_override_weights():
    """UI/UX Designer role overrides default weights giving more emphasis to Projects (35%)."""
    default_w = get_weights("web-developer")
    ui_w = get_weights("ui-ux-designer")

    assert default_w["projects"] == 25
    assert ui_w["projects"] == 35
