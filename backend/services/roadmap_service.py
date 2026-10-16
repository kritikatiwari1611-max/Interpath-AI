from backend.services.role_helper import get_role_by_id
from backend.services.skill_gap_service import analyze_skill_gap

def generate_roadmap(role_id: str, user_skills: list, user_tasks_status: dict = None) -> dict:
    """
    Generates a personalised 4-stage roadmap (Foundation -> Practice -> Project -> Interview)
    dynamically derived from the student's skill gaps in the chosen role.
    
    Data structures used:
    - LIST: ordered stages and tasks
    - DICTIONARY: task status mapping
    - SET: missing and weak skills set for fast stage generation
    """
    if user_tasks_status is None:
        user_tasks_status = {}
        
    role = get_role_by_id(role_id)
    if not role:
        return {"error": "Invalid role"}

    gap_analysis = analyze_skill_gap(role_id, user_skills)
    missing_skills = gap_analysis.get("missing", [])
    weak_skills = gap_analysis.get("needs_improvement", [])
    all_gaps = missing_skills + weak_skills
    
    stages = []
    
    # ---------------- STAGE 1: FOUNDATION ----------------
    stage1_tasks = []
    if missing_skills:
        for idx, skill in enumerate(missing_skills[:4], 1):
            key = f"st1_miss_{skill.lower().replace(' ', '_')}"
            stage1_tasks.append({
                "key": key,
                "title": f"Master Core Concepts of {skill}",
                "description": f"Learn the syntax, core rules, and practical fundamentals of {skill}.",
                "hours": 10,
                "topic": skill,
                "status": user_tasks_status.get(key, "pending")
            })
    else:
        key = "st1_found_review"
        stage1_tasks.append({
            "key": key,
            "title": f"Review Core {role['title']} Foundations",
            "description": "Solidify and revise essential terminology and tools.",
            "hours": 6,
            "topic": "Fundamentals",
            "status": user_tasks_status.get(key, "pending")
        })
        
    stages.append({
        "stage_number": 1,
        "name": "Foundation",
        "badge": "Core Knowledge",
        "description": "Close critical prerequisite and syntax gaps before writing projects.",
        "tasks": stage1_tasks
    })

    # ---------------- STAGE 2: PRACTICE & TOOLS ----------------
    stage2_tasks = []
    if weak_skills:
        for idx, skill in enumerate(weak_skills[:3], 1):
            key = f"st2_weak_{skill.lower().replace(' ', '_')}"
            stage2_tasks.append({
                "key": key,
                "title": f"Hands-on Exercises in {skill}",
                "description": f"Solve practical scenarios and small exercises to elevate {skill} from Beginner to Intermediate.",
                "hours": 12,
                "topic": skill,
                "status": user_tasks_status.get(key, "pending")
            })
    
    # Default tool practice task
    key_tool = f"st2_tool_{role_id}"
    stage2_tasks.append({
        "key": key_tool,
        "title": f"Hands-on Practice with {role['learningTopics'][0] if role['learningTopics'] else 'Domain Tools'}",
        "description": "Complete interactive exercises and mini assignments.",
        "hours": 14,
        "topic": "Domain Exercises",
        "status": user_tasks_status.get(key_tool, "pending")
    })
    
    stages.append({
        "stage_number": 2,
        "name": "Practice & Application",
        "badge": "Skill Elevation",
        "description": "Strengthen intermediate topics with coding or domain exercises.",
        "tasks": stage2_tasks
    })

    # ---------------- STAGE 3: PORTFOLIO PROJECT ----------------
    stage3_tasks = []
    suggested_projects = role.get("suggestedProjects", ["Role Capstone Project"])
    for idx, proj_name in enumerate(suggested_projects[:2], 1):
        key_proj = f"st3_proj_{idx}_{role_id}"
        stage3_tasks.append({
            "key": key_proj,
            "title": f"Build: {proj_name}",
            "description": f"Implement complete project incorporating required skills ({', '.join(all_gaps[:2]) if all_gaps else 'all core skills'}).",
            "hours": 25,
            "topic": "Capstone Project",
            "status": user_tasks_status.get(key_proj, "pending")
        })

    stages.append({
        "stage_number": 3,
        "name": "Project Building",
        "badge": "Portfolio Ready",
        "description": "Create verifiable projects showcasing role-specific problem solving.",
        "tasks": stage3_tasks
    })

    # ---------------- STAGE 4: INTERVIEW PREPARATION ----------------
    stage4_tasks = []
    for idx, topic in enumerate(role.get("interviewTopics", ["Core Concepts"])[:3], 1):
        key_iv = f"st4_iv_{idx}_{role_id}"
        stage4_tasks.append({
            "key": key_iv,
            "title": f"Interview Mastery: {topic}",
            "description": f"Practice technical and conceptual questions covering {topic}.",
            "hours": 8,
            "topic": topic,
            "status": user_tasks_status.get(key_iv, "pending")
        })
    
    # Mock interview practice task
    key_mock = f"st4_mock_{role_id}"
    stage4_tasks.append({
        "key": key_mock,
        "title": f"Complete 2 Full Mock Interviews for {role['title']}",
        "description": "Test yourself under simulated interview conditions with score feedback.",
        "hours": 5,
        "topic": "Mock Interview",
        "status": user_tasks_status.get(key_mock, "pending")
    })

    stages.append({
        "stage_number": 4,
        "name": "Interview Preparation",
        "badge": "Demo Ready",
        "description": "Practice mock interviews, behavioral questions, and explainable project defense.",
        "tasks": stage4_tasks
    })

    # Overall roadmap completion stats
    all_tasks = [t for st in stages for t in st["tasks"]]
    completed_count = sum(1 for t in all_tasks if t["status"] == "completed")
    in_progress_count = sum(1 for t in all_tasks if t["status"] == "in_progress")
    total_tasks = len(all_tasks)
    progress_pct = round((completed_count / total_tasks * 100), 1) if total_tasks > 0 else 0.0

    return {
        "role_id": role["id"],
        "role_title": role["title"],
        "stages": stages,
        "total_tasks": total_tasks,
        "completed_tasks": completed_count,
        "in_progress_tasks": in_progress_count,
        "progress_pct": progress_pct
    }
