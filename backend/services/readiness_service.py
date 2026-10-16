import json
from pathlib import Path
from backend.config import KNOWLEDGE_BASE_DIR

_WEIGHTS_CACHE = {}

def get_weights(role_id: str = None) -> dict:
    """Returns scoring weights, applying per-role overrides if defined."""
    global _WEIGHTS_CACHE
    if not _WEIGHTS_CACHE:
        w_path = KNOWLEDGE_BASE_DIR / "weights.json"
        if w_path.exists():
            with open(w_path, "r", encoding="utf-8") as f:
                _WEIGHTS_CACHE = json.load(f)
        else:
            _WEIGHTS_CACHE = {
                "default_weights": {
                    "skills": 35,
                    "projects": 25,
                    "resume": 15,
                    "interview": 20,
                    "certifications": 5
                },
                "role_overrides": {}
            }
            
    default_w = _WEIGHTS_CACHE.get("default_weights", {})
    overrides = _WEIGHTS_CACHE.get("role_overrides", {})
    if role_id and role_id in overrides:
        return dict(overrides[role_id])
    return dict(default_w)

def calculate_readiness_score(
    role_id: str,
    user_skills: list,
    user_projects: list,
    resume_checklist: dict,
    interview_stats: dict,
    user_certifications: list,
    role_meta: dict
) -> dict:
    """
    Computes a transparent, explainable, deterministic Internship Readiness Score.
    The AI never computes or changes these numbers.
    """
    if not role_id or not role_meta:
        return {
            "provisional": True,
            "overall": 0,
            "category_scores": {},
            "weights": get_weights(),
            "reasons": ["No internship role currently selected."],
            "next_actions": ["Select a target role on the Internship Roles page to unlock your analysis."]
        }

    # Check for empty profile (Provisional)
    if not user_skills and not user_projects:
        return {
            "provisional": True,
            "overall": 10,
            "category_scores": {
                "skills": 0,
                "projects": 0,
                "resume": 0,
                "interview": 0,
                "certifications": 0
            },
            "weights": get_weights(role_id),
            "reasons": ["Profile is incomplete: no skills or projects added yet."],
            "next_actions": [
                "Add your current skills in My Profile.",
                "Log at least one academic or self-directed project."
            ]
        }

    weights = get_weights(role_id)
    
    # 1. SKILLS SCORE (0 to 100)
    from backend.services.skill_gap_service import analyze_skill_gap
    gap_result = analyze_skill_gap(role_id, user_skills)
    skills_score = gap_result["overall_match_pct"]

    # 2. PROJECTS SCORE (0 to 100)
    # A project only counts if it exists AND matches projectKeywords or required skills
    proj_keywords = [k.lower() for k in role_meta.get("projectKeywords", [])]
    req_skills = [s["name"].lower() for s in role_meta.get("requiredSkills", [])]
    match_terms = set(proj_keywords + req_skills)
    
    matched_projects = []
    for p in user_projects:
        searchable_text = f"{p.get('title', '')} {p.get('description', '')} {p.get('tech', '')}".lower()
        if any(term in searchable_text for term in match_terms):
            matched_projects.append(p)
            
    if not matched_projects:
        projects_score = 0.0
    else:
        # Completed = full credit (1.0), in-progress = half credit (0.5)
        # Cap score at 100 with 2 relevant completed projects
        credit = 0.0
        for p in matched_projects:
            if p.get("status") == "completed":
                credit += 50.0
            else:
                credit += 25.0
        projects_score = min(100.0, credit)

    # 3. RESUME SCORE (0 to 100)
    # Equal-point checklist of 6 items (each 16.66% ~ 100 / 6)
    resume_items = [
        "resume_exists",
        "education_listed",
        "matching_skills_listed",
        "relevant_project_included",
        "experience_volunteering",
        "contact_portfolio_links"
    ]
    checked_count = sum(1 for item in resume_items if resume_checklist.get(item) is True)
    resume_score = round((checked_count / len(resume_items)) * 100, 1)

    # 4. INTERVIEW SCORE (0 to 100)
    # Computed from saved interview activity: attempts, accuracy, mock interviews completed
    attempted = interview_stats.get("total_attempts", 0)
    accuracy = interview_stats.get("accuracy", 0.0) # 0 to 100
    mocks_done = interview_stats.get("mock_interviews_done", 0)
    
    # Formula: 40% accuracy + 30% practice volume (up to 15 attempts) + 30% mock interview completion (up to 2 mocks)
    volume_credit = min(30.0, (attempted / 15.0) * 30.0)
    mock_credit = min(30.0, (mocks_done / 2.0) * 30.0)
    acc_credit = (accuracy * 0.40)
    interview_score = round(min(100.0, acc_credit + volume_credit + mock_credit), 1)

    # 5. CERTIFICATIONS SCORE (0 to 100)
    cert_keywords = [c.lower() for c in role_meta.get("relevantCertificationKeywords", [])]
    valid_certs = 0
    for cert in user_certifications:
        c_title = cert.get("title", "").lower()
        if any(ck in c_title for ck in cert_keywords):
            valid_certs += 1
            
    # Each relevant cert grants 50 points, capped at 100
    cert_score = min(100.0, valid_certs * 50.0)

    # WEIGHTED OVERALL CALCULATION
    total_weight = sum(weights.values())
    raw_overall = (
        (skills_score * weights["skills"]) +
        (projects_score * weights["projects"]) +
        (resume_score * weights["resume"]) +
        (interview_score * weights["interview"]) +
        (cert_score * weights["certifications"])
    ) / total_weight

    overall_score = round(raw_overall)
    provisional = False

    # Determine priority improvements and next actions
    next_actions = []
    if skills_score < 60:
        next_actions.append("Practice your core missing skills in the Learning Hub to improve your technical match.")
    if projects_score < 50:
        next_actions.append(f"Build a domain project related to {role_meta.get('title')} to verify your applied abilities.")
    if resume_score < 70:
        next_actions.append("Complete missing items in your Resume Checklist under My Profile.")
    if interview_score < 50:
        next_actions.append("Attempt at least 1 Mock Interview session to establish interview confidence.")
    if not next_actions:
        next_actions.append("Your readiness is stellar! Review your Matched Internships and apply with confidence.")

    return {
        "provisional": provisional,
        "overall": overall_score,
        "role_id": role_id,
        "role_title": role_meta.get("title"),
        "category_scores": {
            "skills": round(skills_score, 1),
            "projects": round(projects_score, 1),
            "resume": round(resume_score, 1),
            "interview": round(interview_score, 1),
            "certifications": round(cert_score, 1)
        },
        "weights": weights,
        "matched_projects_count": len(matched_projects),
        "valid_certifications_count": valid_certs,
        "next_actions": next_actions,
        "disclaimer": "This score estimates preparation. It does not guarantee selection."
    }
