import pytest
from backend.services.matching_service import match_internships

def test_matching_ordering_and_weights():
    """Matching should prioritize internships whose required skills and role match the student."""
    user_skills = [
        {"skill_name": "Python", "level": "Advanced"},
        {"skill_name": "Flask", "level": "Intermediate"},
        {"skill_name": "SQL", "level": "Intermediate"}
    ]
    results = match_internships("python-developer", user_skills, "backend development and APIs")
    
    assert len(results) > 0
    # Top match should be a python-developer role
    top = results[0]
    assert top["role_id"] == "python-developer"
    assert top["match_pct"] >= 70
    assert len(top["matched_skills"]) > 0

def test_matching_detects_missing_skills():
    """Missing skills must be accurately reported on each opportunity."""
    user_skills = [{"skill_name": "Python", "level": "Beginner"}]
    results = match_internships("python-developer", user_skills, "")
    
    for item in results:
        # Every required skill must either be in matched or missing
        all_req = set(item["required_skills"])
        matched_set = set(item["matched_skills"])
        missing_set = set(item["missing_skills"])
        assert matched_set.union(missing_set) == all_req
