-- PostgreSQL / Supabase Schema for InternPath AI

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'student',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS student_profiles (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    course TEXT DEFAULT '',
    specialization TEXT DEFAULT '',
    semester TEXT DEFAULT '',
    college TEXT DEFAULT '',
    career_goal TEXT DEFAULT '',
    interests TEXT DEFAULT '',
    resume_status TEXT DEFAULT 'none',
    resume_checklist_json TEXT DEFAULT '{}',
    github_link TEXT DEFAULT '',
    selected_role_id TEXT DEFAULT '',
    linkedin_link TEXT DEFAULT '',
    portfolio_link TEXT DEFAULT '',
    resume_filename TEXT DEFAULT '',
    resume_original_name TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS user_skills (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill_name TEXT NOT NULL,
    level TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_projects (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    tech TEXT DEFAULT '',
    status TEXT DEFAULT 'completed',
    github_link TEXT DEFAULT '',
    demo_link TEXT DEFAULT '',
    report_filename TEXT DEFAULT '',
    report_original_name TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS user_certifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    issuer TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS roadmap_tasks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id TEXT NOT NULL,
    task_key TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_user_role_task UNIQUE(user_id, role_id, task_key)
);

CREATE TABLE IF NOT EXISTS resource_progress (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    resource_id TEXT NOT NULL,
    completed INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_user_resource UNIQUE(user_id, resource_id)
);

CREATE TABLE IF NOT EXISTS project_progress (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    project_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'saved',
    milestones_done TEXT DEFAULT '[]',
    CONSTRAINT uq_user_project UNIQUE(user_id, project_id)
);

CREATE TABLE IF NOT EXISTS interview_attempts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question_id TEXT NOT NULL,
    role_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    answer TEXT DEFAULT '',
    is_correct INTEGER NOT NULL DEFAULT 0,
    keyword_coverage REAL NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mock_interviews (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id TEXT NOT NULL,
    score INTEGER NOT NULL DEFAULT 0,
    accuracy REAL NOT NULL DEFAULT 0.0,
    weak_topics TEXT DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS readiness_snapshots (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id TEXT NOT NULL,
    overall INTEGER NOT NULL DEFAULT 0,
    breakdown_json TEXT DEFAULT '{}',
    provisional INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    is_read INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_user_skills_user ON user_skills(user_id);
CREATE INDEX IF NOT EXISTS idx_roadmap_tasks_user_role ON roadmap_tasks(user_id, role_id);
CREATE INDEX IF NOT EXISTS idx_interview_attempts_user_topic ON interview_attempts(user_id, topic);
CREATE INDEX IF NOT EXISTS idx_mock_interviews_user_created ON mock_interviews(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_readiness_snapshots_user_created ON readiness_snapshots(user_id, created_at);

-- Row Level Security (RLS enabled as per requirements, no public policies)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_certifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE roadmap_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE resource_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE interview_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE mock_interviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE readiness_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
