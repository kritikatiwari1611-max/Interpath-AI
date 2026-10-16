import json
from werkzeug.security import generate_password_hash
from backend.db import execute_query, init_db

def seed_database():
    """Seeds default demo students, admin user, and initial profiles if database is empty."""
    init_db()
    
    # Check if users already exist
    existing_user = execute_query("SELECT id FROM users LIMIT 1;", fetch_one=True)
    if existing_user:
        print("[seed] Database already seeded. Skipping.")
        return

    print("[seed] Seeding demo users and profiles...")
    
    # 1. Admin User
    admin_pw = generate_password_hash("Admin@123")
    execute_query(
        "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?);",
        ("System Admin", "admin@demo.com", admin_pw, "admin"),
        commit=True
    )
    
    # 2. Student 1: BCA -> Python Developer
    bca_pw = generate_password_hash("Student@123")
    execute_query(
        "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?);",
        ("Aarav Sharma", "student@demo.com", bca_pw, "student"),
        commit=True
    )
    user1 = execute_query("SELECT id FROM users WHERE email = ?;", ("student@demo.com",), fetch_one=True)
    u1_id = user1["id"]
    
    execute_query(
        """INSERT INTO student_profiles 
           (user_id, course, specialization, semester, college, career_goal, interests, resume_status, resume_checklist_json, github_link, selected_role_id) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
        (
            u1_id,
            "BCA",
            "Cloud & Software Development",
            "6th Semester",
            "National Institute of Technology",
            "Become a Backend / Python Software Engineer",
            "AI, Backend APIs, Automation, Data Structures",
            "in_progress",
            json.dumps({
                "resume_exists": True,
                "education_listed": True,
                "matching_skills_listed": True,
                "relevant_project_included": True,
                "experience_volunteering": False,
                "contact_portfolio_links": True
            }),
            "https://github.com/aarav-dev",
            "python-developer"
        ),
        commit=True
    )
    
    # Skills for Aarav
    skills_u1 = [
        ("Python", "Intermediate"),
        ("Flask", "Beginner"),
        ("SQL", "Intermediate"),
        ("Git", "Intermediate"),
        ("Data Structures", "Beginner")
    ]
    for s_name, s_lvl in skills_u1:
        execute_query(
            "INSERT INTO user_skills (user_id, skill_name, level) VALUES (?, ?, ?);",
            (u1_id, s_name, s_lvl),
            commit=True
        )
        
    # Project for Aarav
    execute_query(
        """INSERT INTO user_projects (user_id, title, description, tech, status) 
           VALUES (?, ?, ?, ?, ?);""",
        (u1_id, "Student Attendance REST API", "RESTful backend built using Python and SQLite with token authentication", "Python, Flask, SQLite", "completed"),
        commit=True
    )
    
    # 3. Student 2: B.Com -> Finance Intern
    finance_pw = generate_password_hash("Student@123")
    execute_query(
        "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?);",
        ("Priya Patel", "priya@demo.com", finance_pw, "student"),
        commit=True
    )
    user2 = execute_query("SELECT id FROM users WHERE email = ?;", ("priya@demo.com",), fetch_one=True)
    u2_id = user2["id"]
    
    execute_query(
        """INSERT INTO student_profiles 
           (user_id, course, specialization, semester, college, career_goal, interests, resume_status, resume_checklist_json, github_link, selected_role_id) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
        (
            u2_id,
            "B.Com",
            "Banking & Financial Analysis",
            "4th Semester",
            "Delhi University",
            "Financial Analyst or Corporate Treasury Intern",
            "Corporate Finance, Valuation, Financial Modeling, Stock Markets",
            "ready",
            json.dumps({
                "resume_exists": True,
                "education_listed": True,
                "matching_skills_listed": True,
                "relevant_project_included": True,
                "experience_volunteering": True,
                "contact_portfolio_links": True
            }),
            "https://linkedin.com/in/priya-patel-finance",
            "finance"
        ),
        commit=True
    )
    
    # Skills for Priya (Non-technical: NO programming requirements)
    skills_u2 = [
        ("Financial Modeling", "Beginner"),
        ("Excel & Advanced Formulas", "Intermediate"),
        ("Financial Statement Analysis", "Intermediate"),
        ("Valuation", "Beginner")
    ]
    for s_name, s_lvl in skills_u2:
        execute_query(
            "INSERT INTO user_skills (user_id, skill_name, level) VALUES (?, ?, ?);",
            (u2_id, s_name, s_lvl),
            commit=True
        )
        
    # Project for Priya
    execute_query(
        """INSERT INTO user_projects (user_id, title, description, tech, status) 
           VALUES (?, ?, ?, ?, ?);""",
        (u2_id, "Equity Research Model of Tech Sector", "3-statement financial valuation and DCF analysis of publicly traded IT companies", "Advanced Excel, DCF, Financial Statements", "completed"),
        commit=True
    )
    
    print("[seed] Seeding completed successfully.")

if __name__ == "__main__":
    seed_database()
