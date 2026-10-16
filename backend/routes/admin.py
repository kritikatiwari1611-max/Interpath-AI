from flask import Blueprint, jsonify, session
from backend.db import execute_query
from backend.auth_utils import role_required

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin/stats", methods=["GET"])
@role_required("admin")
def get_admin_stats():
    # User count
    total_users = execute_query("SELECT count(*) as count FROM users WHERE role = 'student'", fetch_one=True)
    
    # Most-selected roles
    role_dist = execute_query(
        """SELECT selected_role_id, count(*) as count 
           FROM student_profiles 
           WHERE selected_role_id != '' 
           GROUP BY selected_role_id 
           ORDER BY count DESC""",
        fetch_all=True
    )
    
    # Average readiness by role
    avg_readiness = execute_query(
        """SELECT role_id, ROUND(AVG(overall), 1) as avg_score, count(*) as snapshot_count 
           FROM readiness_snapshots 
           WHERE role_id != 'none' 
           GROUP BY role_id""",
        fetch_all=True
    )

    # List of users with activity metrics (Admin CANNOT edit student data)
    users = execute_query(
        """SELECT u.id, u.name, u.email, u.created_at, sp.course, sp.selected_role_id,
                  (SELECT count(*) FROM user_skills WHERE user_id = u.id) as skill_count,
                  (SELECT count(*) FROM user_projects WHERE user_id = u.id) as project_count,
                  (SELECT count(*) FROM mock_interviews WHERE user_id = u.id) as mock_count
           FROM users u
           LEFT JOIN student_profiles sp ON u.id = sp.user_id
           WHERE u.role = 'student'
           ORDER BY u.created_at DESC""",
        fetch_all=True
    )

    return jsonify({
        "ok": True,
        "data": {
            "total_students": total_users["count"] if total_users else 0,
            "most_selected_roles": role_dist,
            "avg_readiness_by_role": avg_readiness,
            "students": users
        }
    })
