import os
import sqlite3
from backend.config import DATABASE_URL, DATABASE_PATH, BASE_DIR

# Check if using PostgreSQL (DATABASE_URL provided)
USE_POSTGRES = bool(DATABASE_URL and DATABASE_URL.startswith("postgres"))

if USE_POSTGRES:
    try:
        import psycopg2
        import psycopg2.extras
    except ImportError:
        psycopg2 = None
else:
    psycopg2 = None

def get_connection():
    """Returns a raw database connection based on configuration."""
    if USE_POSTGRES:
        if not psycopg2:
            raise RuntimeError("psycopg2 is required when DATABASE_URL is set.")
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

def execute_query(query: str, params: tuple = (), fetch_one=False, fetch_all=False, commit=False):
    """
    Executes a SQL query cleanly across SQLite and PostgreSQL.
    Translates standard ? placeholders to %s if running on PostgreSQL.
    Returns plain Python dictionaries for rows.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        exec_query = query
        if USE_POSTGRES:
            # Convert ? placeholders to %s for psycopg2
            exec_query = query.replace("?", "%s")
            
        cur.execute(exec_query, params)
        
        last_id = None
        if commit:
            if not USE_POSTGRES:
                last_id = cur.lastrowid
            conn.commit()
            
        if fetch_one:
            row = cur.fetchone()
            if not row:
                return None
            if USE_POSTGRES:
                colnames = [desc[0] for desc in cur.description]
                return dict(zip(colnames, row))
            else:
                return dict(row)
                
        if fetch_all:
            rows = cur.fetchall()
            if USE_POSTGRES:
                colnames = [desc[0] for desc in cur.description]
                return [dict(zip(colnames, r)) for r in rows]
            else:
                return [dict(r) for r in rows]
                
        return last_id
    finally:
        conn.close()

def init_db():
    """Initializes schema if tables do not exist."""
    schema_file = BASE_DIR / "database" / ("schema.postgres.sql" if USE_POSTGRES else "schema.sqlite.sql")
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_file}")
        
    with open(schema_file, "r", encoding="utf-8") as f:
        schema_sql = f.read()
        
    conn = get_connection()
    try:
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute(schema_sql)
            conn.commit()
        else:
            cur.executescript(schema_sql)
            conn.commit()

        # Create study_plans and plan_sessions tables
        if USE_POSTGRES:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS study_plans (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    role_id TEXT NOT NULL,
                    mode TEXT NOT NULL DEFAULT 'demo',
                    inputs_json TEXT NOT NULL DEFAULT '{}',
                    plan_json TEXT NOT NULL DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS plan_sessions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    plan_id INTEGER NOT NULL REFERENCES study_plans(id) ON DELETE CASCADE,
                    session_key TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_plan_sessions_user_plan ON plan_sessions(user_id, plan_id);
            """)
            conn.commit()
        else:
            cur.executescript("""
                CREATE TABLE IF NOT EXISTS study_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    role_id TEXT NOT NULL,
                    mode TEXT NOT NULL DEFAULT 'demo',
                    inputs_json TEXT NOT NULL DEFAULT '{}',
                    plan_json TEXT NOT NULL DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS plan_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    plan_id INTEGER NOT NULL,
                    session_key TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY(plan_id) REFERENCES study_plans(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_plan_sessions_user_plan ON plan_sessions(user_id, plan_id);
            """)
            conn.commit()

        # Seamless migrations for guided flow additions
        migrations = [
            ("student_profiles", "selected_role_id", "TEXT DEFAULT ''"),
            ("student_profiles", "linkedin_link", "TEXT DEFAULT ''"),
            ("student_profiles", "portfolio_link", "TEXT DEFAULT ''"),
            ("student_profiles", "resume_filename", "TEXT DEFAULT ''"),
            ("student_profiles", "resume_original_name", "TEXT DEFAULT ''"),
            ("user_projects", "github_link", "TEXT DEFAULT ''"),
            ("user_projects", "demo_link", "TEXT DEFAULT ''"),
            ("user_projects", "report_filename", "TEXT DEFAULT ''"),
            ("user_projects", "report_original_name", "TEXT DEFAULT ''"),
            ("resource_progress", "status", "TEXT DEFAULT 'pending'"),
            ("interview_attempts", "score", "INTEGER DEFAULT 0"),
            ("interview_attempts", "mode", "TEXT DEFAULT 'demo'"),
            ("interview_attempts", "feedback_json", "TEXT DEFAULT '{}'"),
            ("mock_interviews", "mode", "TEXT DEFAULT 'demo'"),
            ("mock_interviews", "session_id", "TEXT DEFAULT ''"),
            ("mock_interviews", "details_json", "TEXT DEFAULT '[]'"),
            ("mock_interviews", "topic_results", "TEXT DEFAULT '{}'")
        ]
        for tbl, col, col_def in migrations:
            try:
                if USE_POSTGRES:
                    cur.execute(f"ALTER TABLE {tbl} ADD COLUMN IF NOT EXISTS {col} {col_def};")
                else:
                    cur.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} {col_def};")
                conn.commit()
            except Exception:
                # Column already exists
                pass
    finally:
        conn.close()

