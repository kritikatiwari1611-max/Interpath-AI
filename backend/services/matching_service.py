import json
from pathlib import Path
from backend.config import KNOWLEDGE_BASE_DIR

_INTERNSHIPS_CACHE = []

def get_demo_internships() -> list:
    """Loads fictional demo internships from knowledge_base/internships_demo.json."""
    global _INTERNSHIPS_CACHE
    if not _INTERNSHIPS_CACHE:
        path = KNOWLEDGE_BASE_DIR / "internships_demo.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                _INTERNSHIPS_CACHE = json.load(f)
        else:
            _INTERNSHIPS_CACHE = []
    return _INTERNSHIPS_CACHE

def match_internships(user_role_id: str, user_skills: list, user_interests: str) -> list:
    """
    Computes match % for demo internships:
    Match % = skills overlap (60) + role match (25) + interest match (15).
    
    Data structures used:
    - SET: fast intersection of student skills and required internship skills
    - LIST: sorted output ranked by match percentage descending
    """
    all_internships = get_demo_internships()
    # Label: SET DATA STRUCTURE - student skills
    student_skill_names = {s["skill_name"].strip().lower() for s in user_skills}
    interests_tokens = {w.strip().lower() for w in user_interests.replace(",", " ").split() if len(w) > 2}

    results = []
    for item in all_internships:
        req_skills = [sk.strip() for sk in item.get("required_skills", [])]
        req_skills_lower = {sk.lower() for sk in req_skills}
        
        # 1. Skills overlap (up to 60 points)
        matched_skills = [sk for sk in req_skills if sk.lower() in student_skill_names]
        missing_skills = [sk for sk in req_skills if sk.lower() not in student_skill_names]
        
        overlap_ratio = len(matched_skills) / len(req_skills) if req_skills else 1.0
        skills_points = overlap_ratio * 60.0

        # 2. Role match (25 points)
        role_points = 25.0 if item.get("role_id") == user_role_id else 5.0

        # 3. Interest match (up to 15 points)
        desc_tokens = set(f"{item.get('title', '')} {item.get('description', '')}".lower().split())
        interest_overlap = len(interests_tokens.intersection(desc_tokens))
        interest_points = 15.0 if interest_overlap > 0 else 5.0

        total_match_pct = round(skills_points + role_points + interest_points)
        total_match_pct = min(100, max(10, total_match_pct))

        reasons = []
        if item.get("role_id") == user_role_id:
            reasons.append("Exact match with your target internship role.")
        if matched_skills:
            reasons.append(f"You already possess {len(matched_skills)} required skill(s): {', '.join(matched_skills[:3])}.")
        if interest_overlap > 0:
            reasons.append("Aligns directly with your recorded career interests.")

        results.append({
            "id": item["id"],
            "title": item["title"],
            "organization": item["organization"],
            "role_id": item["role_id"],
            "location": item["location"],
            "duration": item["duration"],
            "eligibility": item["eligibility"],
            "description": item["description"],
            "required_skills": req_skills,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "match_pct": total_match_pct,
            "reasons": reasons,
            "demo_label": "Demo data, not live vacancies"
        })

    # Sort descending by match percentage
    results.sort(key=lambda x: x["match_pct"], reverse=True)
    return results
