import json
from flask import Blueprint, request, jsonify, session
from backend.db import execute_query
from backend.auth_utils import login_required

profile_bp = Blueprint("profile", __name__)

@profile_bp.route("/profile", methods=["GET"])
@login_required
def get_profile():
    user_id = session["user_id"]
    profile = execute_query("SELECT * FROM student_profiles WHERE user_id = ?", (user_id,), fetch_one=True)
    if not profile:
        profile = {
            "course": "", "specialization": "", "semester": "", "college": "",
            "career_goal": "", "interests": "", "resume_status": "none",
            "resume_checklist_json": "{}", "github_link": "", "selected_role_id": "",
            "linkedin_link": "", "portfolio_link": "", "resume_filename": "", "resume_original_name": ""
        }
    
    # Parse checklist JSON safely
    try:
        checklist = json.loads(profile.get("resume_checklist_json") or "{}")
    except Exception:
        checklist = {}

    # Fetch skills, projects, and certifications
    skills = execute_query("SELECT id, skill_name, level FROM user_skills WHERE user_id = ?", (user_id,), fetch_all=True)
    projects = execute_query(
        "SELECT id, title, description, tech, status, github_link, demo_link, report_filename, report_original_name FROM user_projects WHERE user_id = ?",
        (user_id,),
        fetch_all=True
    )
    certs = execute_query("SELECT id, title, issuer FROM user_certifications WHERE user_id = ?", (user_id,), fetch_all=True)

    return jsonify({
        "ok": True,
        "data": {
            "profile": {
                "course": profile.get("course", "") or "",
                "specialization": profile.get("specialization", "") or "",
                "semester": profile.get("semester", "") or "",
                "college": profile.get("college", "") or "",
                "career_goal": profile.get("career_goal", "") or "",
                "interests": profile.get("interests", "") or "",
                "resume_status": profile.get("resume_status", "none") or "none",
                "resume_checklist": checklist,
                "github_link": profile.get("github_link", "") or "",
                "linkedin_link": profile.get("linkedin_link", "") or "",
                "portfolio_link": profile.get("portfolio_link", "") or "",
                "resume_filename": profile.get("resume_filename", "") or "",
                "resume_original_name": profile.get("resume_original_name", "") or "",
                "selected_role_id": profile.get("selected_role_id", "") or ""
            },
            "skills": skills,
            "projects": projects,
            "certifications": certs
        }
    })

@profile_bp.route("/profile", methods=["PUT"])
@login_required
def update_profile():
    user_id = session["user_id"]
    data = request.get_json() or {}

    course = data.get("course", "").strip()
    specialization = data.get("specialization", "").strip()
    semester = data.get("semester", "").strip()
    college = data.get("college", "").strip()
    career_goal = data.get("career_goal", "").strip()
    interests = data.get("interests", "").strip()
    github_link = data.get("github_link", "").strip()
    linkedin_link = data.get("linkedin_link", "").strip()
    portfolio_link = data.get("portfolio_link", "").strip()
    resume_checklist = json.dumps(data.get("resume_checklist", {}))

    # URL Validations
    if linkedin_link and not (linkedin_link.startswith("https://www.linkedin.com/") or linkedin_link.startswith("https://linkedin.com/")):
        return jsonify({"ok": False, "error": "LinkedIn URL must start with https://www.linkedin.com/ or https://linkedin.com/"}), 400

    if github_link and not github_link.startswith("https://github.com/"):
        return jsonify({"ok": False, "error": "GitHub URL must start with https://github.com/"}), 400

    # Upsert student profile
    existing = execute_query("SELECT user_id, resume_status, selected_role_id FROM student_profiles WHERE user_id = ?", (user_id,), fetch_one=True)
    
    if "resume_status" in data:
        resume_status = data.get("resume_status")
    elif existing and existing.get("resume_status"):
        resume_status = existing["resume_status"]
    else:
        resume_status = "none"

    if "selected_role_id" in data:
        selected_role_id = data.get("selected_role_id", "").strip()
    elif existing and existing.get("selected_role_id"):
        selected_role_id = existing["selected_role_id"]
    else:
        selected_role_id = ""
    if existing:
        execute_query(
            """UPDATE student_profiles SET 
               course = ?, specialization = ?, semester = ?, college = ?, career_goal = ?, 
               interests = ?, resume_status = ?, resume_checklist_json = ?, github_link = ?, 
               linkedin_link = ?, portfolio_link = ?, selected_role_id = ? 
               WHERE user_id = ?""",
            (course, specialization, semester, college, career_goal, interests, resume_status, resume_checklist, github_link, linkedin_link, portfolio_link, selected_role_id, user_id),
            commit=True
        )
    else:
        execute_query(
            """INSERT INTO student_profiles 
               (user_id, course, specialization, semester, college, career_goal, interests, resume_status, resume_checklist_json, github_link, linkedin_link, portfolio_link, selected_role_id) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, course, specialization, semester, college, career_goal, interests, resume_status, resume_checklist, github_link, linkedin_link, portfolio_link, selected_role_id),
            commit=True
        )

    return jsonify({"ok": True, "data": {"message": "Profile updated successfully."}})

@profile_bp.route("/profile/resume-upload", methods=["POST"])
@login_required
def upload_resume():
    """Secure per-user resume upload adhering strictly to file size and extension checks."""
    import secrets
    from werkzeug.utils import secure_filename
    from backend.config import UPLOADS_DIR, MAX_UPLOAD_SIZE_BYTES, ALLOWED_EXTENSIONS

    user_id = session["user_id"]
    if "resume" not in request.files:
        return jsonify({"ok": False, "error": "No resume file attached in request."}), 400

    file = request.files["resume"]
    if not file or file.filename == "":
        return jsonify({"ok": False, "error": "No selected file."}), 400

    filename = secure_filename(file.filename)
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"ok": False, "error": "Invalid file format. Only PDF (and DOCX) documents are accepted."}), 400

    # Read content and check file size (max 2MB)
    content = file.read()
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        return jsonify({"ok": False, "error": "File size exceeds 2 MB limit."}), 400

    user_folder = UPLOADS_DIR / str(user_id)
    user_folder.mkdir(parents=True, exist_ok=True)

    # Save with random, safe server filename
    safe_name = f"resume_{secrets.token_hex(12)}.{ext}"
    dest_path = user_folder / safe_name
    with open(dest_path, "wb") as f:
        f.write(content)

    # Update database with upsert
    existing = execute_query("SELECT user_id FROM student_profiles WHERE user_id = ?", (user_id,), fetch_one=True)
    if existing:
        execute_query(
            "UPDATE student_profiles SET resume_filename = ?, resume_original_name = ?, resume_status = 'ready' WHERE user_id = ?",
            (safe_name, filename, user_id),
            commit=True
        )
    else:
        execute_query(
            "INSERT INTO student_profiles (user_id, resume_filename, resume_original_name, resume_status) VALUES (?, ?, ?, 'ready')",
            (user_id, safe_name, filename),
            commit=True
        )

    return jsonify({
        "ok": True,
        "data": {
            "message": "Resume uploaded successfully.",
            "filename": safe_name,
            "original_name": filename
        }
    })

@profile_bp.route("/profile/resume-delete", methods=["POST"])
@login_required
def delete_resume():
    """Deletes uploaded resume file and resets profile record."""
    from backend.config import UPLOADS_DIR
    user_id = session["user_id"]
    prof = execute_query("SELECT resume_filename FROM student_profiles WHERE user_id = ?", (user_id,), fetch_one=True)
    if prof and prof.get("resume_filename"):
        file_path = UPLOADS_DIR / str(user_id) / prof["resume_filename"]
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass

    execute_query(
        "UPDATE student_profiles SET resume_filename = '', resume_original_name = '', resume_status = 'none' WHERE user_id = ?",
        (user_id,),
        commit=True
    )
    return jsonify({"ok": True, "data": {"message": "Resume removed."}})

@profile_bp.route("/profile/role", methods=["PUT"])
@login_required
def update_selected_role():
    user_id = session["user_id"]
    data = request.get_json() or {}
    role_id = data.get("role_id", "").strip()

    existing = execute_query("SELECT user_id FROM student_profiles WHERE user_id = ?", (user_id,), fetch_one=True)
    if existing:
        execute_query("UPDATE student_profiles SET selected_role_id = ? WHERE user_id = ?", (role_id, user_id), commit=True)
    else:
        execute_query("INSERT INTO student_profiles (user_id, selected_role_id) VALUES (?, ?)", (user_id, role_id), commit=True)
    return jsonify({"ok": True, "data": {"selected_role_id": role_id}})

