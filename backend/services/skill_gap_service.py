from backend.services.role_helper import get_role_by_id

# Skill proficiency scores
LEVEL_SCORES = {
    "beginner": 0.4,
    "intermediate": 0.7,
    "advanced": 1.0
}

# Importance weight multipliers
IMPORTANCE_WEIGHTS = {
    "core": 3.0,
    "important": 2.0,
    "bonus": 1.0
}

def analyze_skill_gap(role_id: str, user_skills: list) -> dict:
    """
    Performs deterministic skill-gap analysis for a specific role and user skill list.
    
    Data structures used:
    - DICTIONARY: skill lookup by name (lowercase) for O(1) matching
    - SET: fast check of existing student skill names
    - LIST: structured result outputs (learned, needs_improvement, missing, priority_actions)
    """
    role = get_role_by_id(role_id)
    if not role:
        return {
            "role_found": False,
            "overall_match_pct": 0,
            "weighted_score": 0.0,
            "skills": []
        }
        
    # Label: DICTIONARY DATA STRUCTURE - fast lookup by normalized skill name
    user_skill_dict = {s["skill_name"].strip().lower(): s.get("level", "Beginner") for s in user_skills}
    # Label: SET DATA STRUCTURE - student acquired skill set
    user_skill_set = set(user_skill_dict.keys())

    required_skills = role.get("requiredSkills", [])
    
    total_possible_weight = 0.0
    accumulated_weight = 0.0
    
    # Label: LIST DATA STRUCTURE - categorized results
    learned_list = []
    needs_improvement_list = []
    missing_list = []
    priority_gaps = []
    all_skill_details = []

    for req in required_skills:
        req_name = req["name"]
        norm_name = req_name.strip().lower()
        importance = req.get("importance", "important").lower()
        imp_multiplier = IMPORTANCE_WEIGHTS.get(importance, 2.0)
        
        total_possible_weight += (imp_multiplier * 1.0)
        
        if norm_name in user_skill_set:
            level = user_skill_dict[norm_name]
            score_multiplier = LEVEL_SCORES.get(level.lower(), 0.4)
            accumulated_weight += (imp_multiplier * score_multiplier)
            
            if level.lower() == "advanced":
                status = "Strong"
                learned_list.append(req_name)
            elif level.lower() == "intermediate":
                status = "Good"
                learned_list.append(req_name)
            else:
                status = "Needs improvement"
                needs_improvement_list.append(req_name)
                if importance == "core":
                    priority_gaps.append(req_name)
        else:
            status = "Missing"
            missing_list.append(req_name)
            if importance == "core":
                priority_gaps.append(req_name)
                
        all_skill_details.append({
            "name": req_name,
            "importance": importance,
            "status": status,
            "user_level": user_skill_dict.get(norm_name, "None")
        })

    # Calculate deterministic percentage (0 - 100)
    match_pct = round((accumulated_weight / total_possible_weight * 100), 1) if total_possible_weight > 0 else 0.0
    
    # Suggested actions based on priority gaps
    suggested_actions = []
    if priority_gaps:
        for gap in priority_gaps[:3]:
            suggested_actions.append(f"Focus immediately on '{gap}' — it is a core prerequisite for {role['title']}.")
    else:
        suggested_actions.append(f"Excellent foundation! Advance your practical project experience in {role['title']}.")

    return {
        "role_found": True,
        "role_id": role["id"],
        "role_title": role["title"],
        "overall_match_pct": match_pct,
        "learned": learned_list,
        "needs_improvement": needs_improvement_list,
        "missing": missing_list,
        "priority_gaps": priority_gaps,
        "suggested_actions": suggested_actions,
        "skills": all_skill_details
    }
