import json
from pathlib import Path
from backend.config import KNOWLEDGE_BASE_DIR
from backend.services.role_helper import get_role_by_id
from backend.services.skill_gap_service import analyze_skill_gap
from backend.services import ai_service

_RESOURCES_CACHE = []

def get_all_resources() -> list:
    """Loads learning resources from knowledge_base/resources.json."""
    global _RESOURCES_CACHE
    if not _RESOURCES_CACHE:
        res_path = KNOWLEDGE_BASE_DIR / "resources.json"
        if res_path.exists():
            with open(res_path, "r", encoding="utf-8") as f:
                _RESOURCES_CACHE = json.load(f)
        else:
            _RESOURCES_CACHE = []
    return _RESOURCES_CACHE


def load_resources_map() -> dict:
    """Returns a dictionary mapping resource ID to resource object for fast O(1) lookups."""
    return {r["id"]: r for r in get_all_resources()}


def generate_roadmap(role_id: str, user_skills: list, user_tasks_status: dict = None) -> dict:
    """
    Generates a personalised 4-stage roadmap (Foundation -> Practice -> Project -> Interview)
    dynamically derived from the student's skill gaps in the chosen role.
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
        "title": f"Hands-on Practice with {role['learningTopics'][0] if role.get('learningTopics') else 'Domain Tools'}",
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


# -----------------------------------------------------------------------------
# SKILL EXPLANATIONS ("Why this skill matters")
# -----------------------------------------------------------------------------

# Curated domain rationale for technical and non-technical skills
SKILL_EXPLANATION_KB = {
    "Python": {
        "why": "Python is the industry standard for backend APIs, data pipelines, automation, and AI integration due to its readable syntax and rich ecosystem.",
        "how": "Used to write backend business logic, query databases, automate tasks, and build REST APIs with frameworks like Flask or FastAPI.",
    },
    "Flask": {
        "why": "Flask provides an unopinionated, lightweight framework to understand HTTP request handling, decorators, and routing without hidden magic.",
        "how": "Used to construct REST API endpoints, serialize JSON responses, handle CORS, and connect frontends with relational databases.",
    },
    "SQL": {
        "why": "SQL is essential for managing structured data, performing joins, aggregations, and running performant queries across relational databases.",
        "how": "Used to fetch and update application state, design normalized schemas, and aggregate analytics for reporting.",
    },
    "Git": {
        "why": "Version control with Git is a mandatory requirement across every professional software engineering team in the world.",
        "how": "Used to create branches, review pull requests, roll back breaking changes, and collaborate on production codebases.",
    },
    "HTML5": {
        "why": "HTML5 provides semantic structure and accessibility for web applications across mobile and desktop browsers.",
        "how": "Used to organize page hierarchy, forms, modals, tables, and media elements cleanly.",
    },
    "CSS3": {
        "why": "CSS3 governs layout responsiveness, typography, design systems, and visual feedback across diverse screen dimensions.",
        "how": "Used with Flexbox and CSS Grid to structure responsive interfaces and provide clean UI states.",
    },
    "JavaScript": {
        "why": "JavaScript is the universal runtime powering dynamic client-side interactivity, asynchronous API calls, and web components.",
        "how": "Used to handle DOM events, make fetch() requests to backend endpoints, and update views without reloading.",
    },
    "REST APIs": {
        "why": "REST APIs define the contract for how distributed systems, client frontends, and backend microservices exchange data.",
        "how": "Used to structure standard GET, POST, PUT, DELETE endpoints with predictable HTTP status codes and JSON payloads.",
    },
    "Financial Statement Analysis": {
        "why": "Understanding Income Statements, Balance Sheets, and Cash Flow Statements is the core foundation of corporate finance and valuation.",
        "how": "Used to audit historical financial performance, trace cash liquidity, and evaluate capital structure health.",
    },
    "Financial Modeling": {
        "why": "Financial modeling converts business assumptions into dynamic multi-year operational forecasts and valuation simulations.",
        "how": "Used in Excel to link three-statement models, build sensitivity tables, and project free cash flows.",
    },
    "Valuation": {
        "why": "Valuation methods (DCF, comparable multiples) allow analysts to determine whether assets and companies are fairly priced.",
        "how": "Used to calculate enterprise value, discount cash flows with WACC, and advise on investment decisions.",
    },
    "Excel & Advanced Formulas": {
        "why": "Excel remains the primary working canvas for financial analysts, business planners, and operational managers globally.",
        "how": "Used to organize datasets with XLOOKUP, INDEX/MATCH, dynamic arrays, and audit financial calculations.",
    },
    "Data Cleaning": {
        "why": "Real-world data is messy, incomplete, and full of outliers; analysis on uncleaned data produces misleading business decisions.",
        "how": "Used to detect null values, handle categorical encoding, remove duplicates, and impute missing figures.",
    },
    "PowerBI & Tableau": {
        "why": "Visual analytics turn dense database tables into intuitive dashboards that non-technical business leaders can act upon.",
        "how": "Used to build interactive charts, drill-down KPIs, and automate monthly executive reporting.",
    },
    "SEO": {
        "why": "Search Engine Optimization drives sustainable, organic customer acquisition without recurring paid advertising costs.",
        "how": "Used to optimize on-page meta tags, schema markup, search intent keywords, and build high-quality backlink authority.",
    },
    "Performance Marketing": {
        "why": "Direct paid campaigns require quantitative tracking to ensure advertising spend generates positive Return on Ad Spend (ROAS).",
        "how": "Used to analyze Click-Through Rates (CTR), Conversion Rates (CVR), and cost-per-acquisition across Google and Meta ad platforms.",
    },
    "Recruitment Lifecycle": {
        "why": "Talent acquisition strategy determines an organization's capability, workforce culture, and operational scaling velocity.",
        "how": "Used to source candidates, conduct preliminary cultural screens, coordinate interviewer panels, and manage offers.",
    },
    "People Operations": {
        "why": "Structured employee onboarding and retention programs directly prevent employee churn and boost first-year productivity.",
        "how": "Used to design 30-60-90 day onboarding plans, conduct performance appraisals, and foster positive workplace culture.",
    }
}

def get_skill_explanations(role_id: str, user_skills: list) -> list:
    """
    Returns why-it-matters explanations for each missing or low-level skill in the student's gap analysis.
    """
    role = get_role_by_id(role_id)
    if not role:
        return []

    gap_analysis = analyze_skill_gap(role_id, user_skills)
    missing = set(gap_analysis.get("missing", []))
    weak = set(gap_analysis.get("needs_improvement", []))

    explanations = []
    for skill_item in role.get("requiredSkills", []):
        s_name = skill_item["name"]
        is_missing = s_name in missing
        is_weak = s_name in weak

        if not (is_missing or is_weak):
            continue  # Skip already known skills (Medium or High)

        # Lookup in curated explanations or build safe fallback
        kb_entry = SKILL_EXPLANATION_KB.get(s_name, {})
        why_matters = kb_entry.get("why") or f"{s_name} is a {skill_item.get('importance', 'core')} competency required for {role.get('title', 'this role')}."
        how_used = kb_entry.get("how") or f"Used on a daily basis to execute essential {role.get('title', 'domain')} workflows and deliverables."
        
        starting_point = (
            "Starting from scratch (Missing skill — prioritize foundation tutorials)."
            if is_missing else
            "Level up from Beginner (Low proficiency — focus on hands-on practical exercises)."
        )

        explanations.append({
            "skill": s_name,
            "importance": skill_item.get("importance", "important"),
            "why_it_matters": why_matters,
            "how_it_is_used_in_role": how_used,
            "your_starting_point": starting_point
        })

    return explanations


# -----------------------------------------------------------------------------
# WEEKLY STUDY PLAN GENERATION (Rule-Based Demo Generator & AI Orchestration)
# -----------------------------------------------------------------------------

def skill_sort_is_core(skill_name: str, role: dict) -> bool:
    """Returns True if the skill is marked as 'core' in the role requirements."""
    for s in role.get("requiredSkills", []):
        if s.get("name", "").lower() == skill_name.lower():
            return s.get("importance", "").lower() == "core"
    return False


def build_rule_based_study_plan(student_context: dict) -> dict:
    """
    Deterministically generates a structured weekly study plan matching the student's
    available hours, learning style, and skill gaps without calling any external API.
    """
    role_id = student_context.get("role_id", "python-developer")
    role = get_role_by_id(role_id) or {"title": "Software Developer", "category": "Technical"}
    role_title = role.get("title", "Career Role")
    hours_per_week = int(student_context.get("hours_per_week", 10))
    weeks_count = int(student_context.get("weeks", 6))
    learning_style = student_context.get("learning_style", "Videos first")
    skills = student_context.get("skills", [])

    # Identify skill gaps
    gap_analysis = analyze_skill_gap(role_id, skills)
    missing_skills = gap_analysis.get("missing", [])
    weak_skills = gap_analysis.get("needs_improvement", [])
    known_skills = gap_analysis.get("learned", [])

    # Order skills: Core gaps first, then Important, then Bonus
    skill_importance_map = {s["name"]: s.get("importance", "important") for s in role.get("requiredSkills", [])}
    
    def skill_sort_key(s):
        imp = skill_importance_map.get(s, "important")
        is_miss = 0 if s in missing_skills else 1
        imp_rank = 0 if imp == "core" else (1 if imp == "important" else 2)
        return (imp_rank, is_miss)

    priority_gaps = sorted(missing_skills + weak_skills, key=skill_sort_key)
    if not priority_gaps:
        priority_gaps = [s["name"] for s in role.get("requiredSkills", [])[:3]]

    # Load available resources mapped by skill and category
    all_resources = get_all_resources()
    resource_by_skill = {}
    for r in all_resources:
        s = r.get("skill")
        if s:
            resource_by_skill.setdefault(s, []).append(r)

    # Distribute gap skills across weeks
    # Allocate weeks: Weeks 1..(N-2) for skills, Week N-1 for Project, Week N for Interview
    skill_weeks_count = max(1, weeks_count - 2) if weeks_count >= 4 else max(1, weeks_count - 1)
    
    weeks = []
    max_weekly_minutes = hours_per_week * 60

    # Distribute skills into chunks
    skill_chunks = [[] for _ in range(skill_weeks_count)]
    for idx, skill in enumerate(priority_gaps):
        chunk_idx = idx % skill_weeks_count
        skill_chunks[chunk_idx].append(skill)

    # Build weekly sessions
    for w_idx in range(skill_weeks_count):
        week_num = w_idx + 1
        w_skills = skill_chunks[w_idx] if skill_chunks[w_idx] else [priority_gaps[0]]
        theme = f"Mastering {', '.join(w_skills)}" if len(w_skills) <= 2 else f"Foundations: {w_skills[0]} & Related Tools"
        goal = f"Build solid hands-on competency in {', '.join(w_skills)} through practical exercises."

        sessions = []
        minutes_used = 0

        # If Week 1 and student has known Medium/High skills, add a quick 30-min revision session
        if week_num == 1 and known_skills:
            rev_skill = known_skills[0]
            sessions.append({
                "session_key": f"w{week_num}_s0_rev_{rev_skill.lower().replace(' ', '_')}",
                "title": f"Quick Revision: {rev_skill} Fundamentals",
                "skill": rev_skill,
                "minutes": 30,
                "task_type": "learn",
                "resource_ids": []
            })
            minutes_used += 30

        # Create sessions for each skill in this week according to learning style
        for s in w_skills:
            s_resources = resource_by_skill.get(s, [])
            
            # Sort resources according to student's chosen learning style
            def style_priority(r):
                cat = r.get("category", "")
                if "video" in learning_style.lower():
                    return 0 if cat == "video" else (1 if cat == "docs" else 2)
                elif "notes" in learning_style.lower():
                    return 0 if cat == "docs" else (1 if cat == "video" else 2)
                else:  # Practice first
                    return 0 if cat == "practice" else (1 if cat == "docs" else 2)

            sorted_res = sorted(s_resources, key=style_priority)
            
            if sorted_res:
                for r_idx, res in enumerate(sorted_res[:2]):
                    res_mins = 45
                    if minutes_used + res_mins <= max_weekly_minutes:
                        sessions.append({
                            "session_key": f"w{week_num}_s{len(sessions)+1}_{s.lower().replace(' ', '_')}_{res['category']}",
                            "title": f"{res.get('category', 'Study').title()}: {res.get('title', s)}",
                            "skill": s,
                            "minutes": res_mins,
                            "task_type": "learn" if res.get("category") in ["video", "docs"] else "practice",
                            "resource_ids": [res["id"]]
                        })
                        minutes_used += res_mins
            else:
                # Fallback session when no specific resource exists
                for act_name, act_mins, act_type in [
                    (f"Core Concepts and Documentation of {s}", 60, "learn"),
                    (f"Practical Problem Solving in {s}", 60, "practice")
                ]:
                    if minutes_used + act_mins <= max_weekly_minutes:
                        sessions.append({
                            "session_key": f"w{week_num}_s{len(sessions)+1}_{s.lower().replace(' ', '_')}_{act_type}",
                            "title": act_name,
                            "skill": s,
                            "minutes": act_mins,
                            "task_type": act_type,
                            "resource_ids": []
                        })
                        minutes_used += act_mins

        weeks.append({
            "week": week_num,
            "theme": theme,
            "goal": goal,
            "skills": w_skills,
            "sessions": sessions,
            "total_minutes": minutes_used,
            "total_hours": round(minutes_used / 60, 1),
            "checkpoint": f"Complete a small practical mini-task demonstrating {w_skills[0]} without referring to solution notes.",
            "tip": f"Allocate consistent 45-minute daily slots rather than cramming {w_skills[0]} in one weekend sitting."
        })

    # Portfolio Project Week (Second to last week)
    if weeks_count >= 4:
        proj_week_num = len(weeks) + 1
        proj_name = role.get("suggestedProjects", ["Role Capstone Portfolio Project"])[0]
        proj_sessions = [
            {
                "session_key": f"w{proj_week_num}_s1_proj_setup",
                "title": f"Setup & Architecture: {proj_name}",
                "skill": priority_gaps[0] if priority_gaps else "Architecture",
                "minutes": 60,
                "task_type": "project",
                "resource_ids": []
            },
            {
                "session_key": f"w{proj_week_num}_s2_proj_core",
                "title": f"Core Implementation & Milestone Deliverable",
                "skill": priority_gaps[0] if priority_gaps else "Implementation",
                "minutes": 90,
                "task_type": "project",
                "resource_ids": []
            },
            {
                "session_key": f"w{proj_week_num}_s3_proj_deploy",
                "title": f"Project Testing, Documentation, and GitHub Commit",
                "skill": "Git",
                "minutes": 60,
                "task_type": "project",
                "resource_ids": []
            }
        ]
        total_p_mins = sum(s["minutes"] for s in proj_sessions)
        weeks.append({
            "week": proj_week_num,
            "theme": "Portfolio Project Milestone",
            "goal": f"Build and host {proj_name} showcasing practical skills acquired in earlier weeks.",
            "skills": priority_gaps[:2] if len(priority_gaps) >= 2 else priority_gaps,
            "sessions": proj_sessions,
            "total_minutes": total_p_mins,
            "total_hours": round(total_p_mins / 60, 1),
            "checkpoint": "Ensure your project repo has a clean README with setup instructions and a working demo.",
            "tip": "Commit your code frequently with descriptive messages (e.g. 'Add schema migration' rather than 'update')."
        })

    # Interview Mastery & Revision Week (Final week)
    final_week_num = len(weeks) + 1
    final_sessions = [
        {
            "session_key": f"w{final_week_num}_s1_rev",
            "title": f"Comprehensive Revision of Core {role_title} Concepts",
            "skill": priority_gaps[0] if priority_gaps else "Core Revision",
            "minutes": 60,
            "task_type": "learn",
            "resource_ids": []
        },
        {
            "session_key": f"w{final_week_num}_s2_mock",
            "title": f"Simulated AI Mock Interview (Technical & Behavioral)",
            "skill": "Interview Preparation",
            "minutes": 45,
            "task_type": "interview",
            "resource_ids": []
        },
        {
            "session_key": f"w{final_week_num}_s3_weak_drill",
            "title": f"Targeted Drill on Weak Interview Topics",
            "skill": "Interview Preparation",
            "minutes": 45,
            "task_type": "interview",
            "resource_ids": []
        }
    ]
    total_f_mins = sum(s["minutes"] for s in final_sessions)
    weeks.append({
        "week": final_week_num,
        "theme": "Interview Readiness & Final Review",
        "goal": f"Test yourself under realistic interview conditions for {role_title} and polish project defense answers.",
        "skills": ["Interview Preparation"],
        "sessions": final_sessions,
        "total_minutes": total_f_mins,
        "total_hours": round(total_f_mins / 60, 1),
        "checkpoint": "Score at least 70% on a full 5-question mock interview in the Interview Prep module.",
        "tip": "Structure your verbal and written answers using the STAR format (Situation, Task, Action, Result)."
    })

    # Generate skill explanations
    explanations = get_skill_explanations(role_id, skills)

    return {
        "overview": f"A structured {weeks_count}-week study plan tailored for {role_title} dedicating {hours_per_week} hours/week to close your core priority skill gaps.",
        "skill_explanations": explanations,
        "weeks": weeks[:weeks_count],
        "revision_tips": [
            "Use active recall: quiz yourself on key concepts before looking at solutions.",
            "Space your learning: review difficult syntax 2 days and 7 days after first exposure.",
            "Pair every 45 minutes of theory with at least 15 minutes of hands-on coding or calculation."
        ],
        "confidence_note": "Rule-based pacing optimized for steady weekly milestone mastery without burn-out.",
        "mode": "demo",
        "badge": "Demo mode (rule-based)",
        "notice": "This plan is a suggestion generated from your inputs. It can contain mistakes. Adjust it to your schedule."
    }


def generate_study_plan(student_context: dict, mode: str = "demo") -> dict:
    """
    Unified function for generating a personalized weekly study plan.
    Validates hours and weeks on the server.
    In AI mode: prompts OpenAI, enforces strict JSON validation, removes unknown resource IDs,
    ensures non-technical roles have no coding, and recalculates weekly minutes on the server.
    Gracefully falls back to the deterministic rule-based generator if AI is unavailable.
    """
    # 1. Server validation of inputs (allowed values only)
    allowed_hours = [5, 10, 15, 20]
    allowed_weeks = [4, 6, 8, 12]

    try:
        hours_per_week = int(student_context.get("hours_per_week", 10))
    except (ValueError, TypeError):
        hours_per_week = 10
    if hours_per_week not in allowed_hours:
        hours_per_week = 10
    student_context["hours_per_week"] = hours_per_week

    try:
        weeks_count = int(student_context.get("weeks", 6))
    except (ValueError, TypeError):
        weeks_count = 6
    if weeks_count not in allowed_weeks:
        weeks_count = 6
    student_context["weeks"] = weeks_count

    learning_style = student_context.get("learning_style", "Videos first")
    if learning_style not in ["Videos first", "Notes first", "Practice first"]:
        learning_style = "Videos first"
    student_context["learning_style"] = learning_style

    role_id = student_context.get("role_id", "python-developer")
    role = get_role_by_id(role_id) or {"title": "Software Developer", "category": "Technical"}
    student_context["role_title"] = role.get("title", "Career Track")

    # Fast resource dictionary lookup: { resource_id: resource_data }
    all_resources = get_all_resources()
    resource_map = {r["id"]: r for r in all_resources}
    student_context["available_resources"] = [r for r in all_resources if r.get("role_id") == role_id or r.get("role_id") == "all"]

    skills = student_context.get("skills", [])
    gap_analysis = analyze_skill_gap(role_id, skills)
    student_context["missing_skills"] = gap_analysis.get("missing", [])
    student_context["weak_skills"] = gap_analysis.get("needs_improvement", [])
    known_skills = set(gap_analysis.get("learned", []))

    # Strict non-technical role enforcement
    NON_TECH_ROLES = {"finance", "human-resources", "digital-marketing", "business-analyst"}
    is_non_tech = role_id in NON_TECH_ROLES

    # 2. AI Mode Execution
    if mode == "openai":
        ai_plan = ai_service.call_ai_study_plan(student_context)
        if ai_plan and "weeks" in ai_plan and isinstance(ai_plan["weeks"], list):
            # Server Validation of AI Plan
            sanitized_weeks = []
            planned_skills = set()
            max_minutes = hours_per_week * 60

            for w in ai_plan.get("weeks", [])[:weeks_count]:
                week_num = int(w.get("week", len(sanitized_weeks) + 1))
                theme = str(w.get("theme", f"Week {week_num} Focus"))[:100]
                goal = str(w.get("goal", "Complete assigned study tasks"))[:200]
                w_skills = [str(s)[:50] for s in w.get("skills", [])]
                
                # Filter out programming skills for non-tech roles
                if is_non_tech:
                    w_skills = [s for s in w_skills if not any(c in s.lower() for c in ["python", "java", "coding", "syntax", "c++", "django"])]

                sanitized_sessions = []
                week_minutes = 0

                for s_idx, s in enumerate(w.get("sessions", [])):
                    s_title = str(s.get("title", "Study Session"))[:120]
                    s_mins = max(15, min(120, int(s.get("minutes", 45))))
                    
                    # Validate resource IDs: remove any unknown ID
                    raw_rids = s.get("resource_ids", [])
                    valid_rids = [rid for rid in raw_rids if rid in resource_map]

                    # Enforce that skills already marked MEDIUM or HIGH are not scheduled as new learning
                    session_skill = s.get("skill") or (w_skills[0] if w_skills else "")
                    task_type = s.get("task_type", "learn")
                    if session_skill in known_skills and task_type == "learn":
                        continue

                    # Server recalculates minutes: trim if exceeding hours limit
                    if week_minutes + s_mins > max_minutes and len(sanitized_sessions) >= 2:
                        continue  # Trim sessions exceeding the weekly hours limit

                    session_key = f"w{week_num}_s{s_idx+1}_{session_skill.lower().replace(' ', '_')}"
                    sanitized_sessions.append({
                        "session_key": session_key,
                        "title": s_title,
                        "skill": session_skill,
                        "minutes": s_mins,
                        "task_type": task_type,
                        "resource_ids": valid_rids
                    })
                    week_minutes += s_mins
                    if session_skill:
                        planned_skills.add(session_skill)

                sanitized_weeks.append({
                    "week": week_num,
                    "theme": theme,
                    "goal": goal,
                    "skills": w_skills,
                    "sessions": sanitized_sessions,
                    "total_minutes": week_minutes,
                    "total_hours": round(week_minutes / 60, 1),
                    "checkpoint": str(w.get("checkpoint", "Review key takeaways from this week"))[:150],
                    "tip": str(w.get("tip", "Stay consistent with daily practice slots"))[:150]
                })

            # Check that every Missing or LOW core skill appears in the plan
            core_missing = [s for s in student_context["missing_skills"] + student_context["weak_skills"] if skill_sort_is_core(s, role)]
            for cms in core_missing:
                if cms not in planned_skills and sanitized_weeks:
                    # Append missing core skill to the last suitable week
                    target_week = sanitized_weeks[min(len(sanitized_weeks) - 1, 1)]

                    # If target week is full, replace an existing session to respect max_minutes
                    if target_week["total_minutes"] + 45 > max_minutes and len(target_week["sessions"]) > 1:
                        target_week["sessions"].pop()
                        target_week["total_minutes"] = sum(s["minutes"] for s in target_week["sessions"])

                    target_week["sessions"].append({
                        "session_key": f"w{target_week['week']}_s_core_{cms.lower().replace(' ', '_')}",
                        "title": f"Core Focus: {cms} Mastery",
                        "skill": cms,
                        "minutes": 45,
                        "task_type": "practice",
                        "resource_ids": [r["id"] for r in student_context["available_resources"] if r.get("skill") == cms][:1]
                    })
                    target_week["total_minutes"] += 45
                    target_week["total_hours"] = round(target_week["total_minutes"] / 60, 1)

            # Ensure skill explanations exist
            explanations = ai_plan.get("skill_explanations")
            if not explanations or not isinstance(explanations, list) or len(explanations) == 0:
                explanations = get_skill_explanations(role_id, skills)

            return {
                "overview": str(ai_plan.get("overview", f"AI-generated {weeks_count}-week structured study plan for {student_context['role_title']}."))[:300],
                "skill_explanations": explanations,
                "weeks": sanitized_weeks,
                "revision_tips": [str(t)[:150] for t in ai_plan.get("revision_tips", [])[:3]],
                "confidence_note": str(ai_plan.get("confidence_note", "Personalized based on role gaps and time allocation."))[:200],
                "mode": "openai",
                "badge": "AI mode",
                "notice": "This plan is a suggestion generated from your inputs. It can contain mistakes. Adjust it to your schedule."
            }

    # 3. Demo Mode (Rule-based offline generator fallback)
    return build_rule_based_study_plan(student_context)


def skill_sort_is_core(skill_name: str, role: dict) -> bool:
    """Helper returning True if the skill is labeled 'core' in role requirements."""
    for req in role.get("requiredSkills", []):
        if req["name"].lower() == skill_name.lower() and req.get("importance") == "core":
            return True
    return False
