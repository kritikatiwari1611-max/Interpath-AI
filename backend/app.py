import os
import secrets
from flask import Flask, send_from_directory, jsonify, session, request
from backend.config import SECRET_KEY, BASE_DIR, FRONTEND_DIR

# Import blueprints
from backend.routes.auth import auth_bp
from backend.routes.profile import profile_bp
from backend.routes.roles import roles_bp
from backend.routes.skillgap import skillgap_bp
from backend.routes.roadmap import roadmap_bp
from backend.routes.resources import resources_bp
from backend.routes.projects import projects_bp
from backend.routes.interview import interview_bp
from backend.routes.progress import progress_bp
from backend.routes.readiness import readiness_bp
from backend.routes.internships import internships_bp
from backend.routes.admin import admin_bp
from backend.routes.settings import settings_bp
from backend.routes.health import health_bp

def create_app():
    # Ensure database schema, migrations, and initial seed data exist (critical for cloud deployment)
    try:
        from backend.db import init_db
        from database.seed import seed_database
        init_db()
        seed_database()
    except Exception as e:
        print(f"[create_app] Database setup notice: {e}")

    app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # Register API blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(profile_bp, url_prefix="/api")
    app.register_blueprint(roles_bp, url_prefix="/api")
    app.register_blueprint(skillgap_bp, url_prefix="/api")
    app.register_blueprint(roadmap_bp, url_prefix="/api")
    app.register_blueprint(resources_bp, url_prefix="/api")
    app.register_blueprint(projects_bp, url_prefix="/api")
    app.register_blueprint(interview_bp, url_prefix="/api")
    app.register_blueprint(progress_bp, url_prefix="/api")
    app.register_blueprint(readiness_bp, url_prefix="/api")
    app.register_blueprint(internships_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/api")
    app.register_blueprint(settings_bp, url_prefix="/api")
    app.register_blueprint(health_bp, url_prefix="/api")

    # Security Headers and CSRF Token issuance
    @app.before_request
    def handle_csrf():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_hex(20)
            
        # Protect state-changing mutating requests if user is logged in
        if request.method in ("POST", "PUT", "DELETE"):
            # Exclude login/register from strict CSRF header check for simple API ease
            if not request.path.startswith("/api/auth/login") and not request.path.startswith("/api/auth/register"):
                sent_token = request.headers.get("X-CSRF-Token")
                expected_token = session.get("csrf_token")
                if expected_token and sent_token and sent_token != expected_token:
                    return jsonify({"ok": False, "error": "Invalid CSRF verification token."}), 403

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Pass CSRF token in header so frontend vanilla JS can read and store it
        if "csrf_token" in session:
            response.headers["X-CSRF-Token"] = session["csrf_token"]
        return response

    # Frontend Page Serving Routes
    @app.route("/")
    def index():
        return send_from_directory(str(FRONTEND_DIR), "index.html")

    @app.route("/pages/<path:filename>")
    def serve_pages(filename):
        return send_from_directory(str(FRONTEND_DIR / "pages"), filename)

    @app.route("/css/<path:filename>")
    def serve_css(filename):
        return send_from_directory(str(FRONTEND_DIR / "css"), filename)

    @app.route("/js/<path:filename>")
    def serve_js(filename):
        return send_from_directory(str(FRONTEND_DIR / "js"), filename)

    @app.route("/assets/<path:filename>")
    def serve_assets(filename):
        return send_from_directory(str(FRONTEND_DIR / "assets"), filename)

    @app.route("/manifest.json")
    def serve_manifest():
        return send_from_directory(str(FRONTEND_DIR), "manifest.json")

    @app.route("/sw.js")
    def serve_sw():
        return send_from_directory(str(FRONTEND_DIR), "sw.js")

    @app.route("/api/uploads/<path:filename>")
    def serve_user_upload(filename):
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"ok": False, "error": "Unauthorized"}), 401
        from backend.config import UPLOADS_DIR
        user_folder = UPLOADS_DIR / str(user_id)
        return send_from_directory(str(user_folder), filename)

    return app
