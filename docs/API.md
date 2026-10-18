# InternPath AI - API Documentation

All responses are returned as structured JSON:
`{ "ok": boolean, "data": object | array, "error": string }`

---

### Authentication Routes (`/api/auth`)
* `POST /api/auth/register`: Create a new student account. Body: `{ name, email, password, course, career_goal }`. Returns 201 Created.
* `POST /api/auth/login`: Authenticate student or admin. Enforces 5-attempt rate-limiting lockout. Returns user record and session cookie.
* `POST /api/auth/logout`: Clears session cookie.
* `GET /api/auth/me`: Returns current authenticated user record.

### Profile & Skills (`/api`)
* `GET /api/profile`: Returns student profile details, skill list, projects, and certifications.
* `PUT /api/profile`: Updates profile details and resume checklist items.
* `PUT /api/profile/role`: Updates selected target internship role ID.
* `GET /api/skill-gap`: Returns deterministic skill gap analysis for the user's selected role.
* `PUT /api/skills`: Replaces user skills. Body: `{ skills: [{ name, level }] }`.

### Roles, Roadmap & AI Weekly Study Plan (`/api`)
* `GET /api/roles`: Returns all 12+ roles from the knowledge base.
* `GET /api/roles/<role_id>`: Returns details and prerequisites of a single role.
* `GET /api/roadmap`: Generates the personalized 4-stage roadmap based on student gaps.
* `PUT /api/roadmap/tasks/<task_key>`: Updates task status (`pending`, `in_progress`, `completed`).
* `GET /api/roadmap/skill-explanations`: Returns personalized why-it-matters metadata for current skill gaps (`why_it_matters`, `how_it_is_used_in_role`, `your_starting_point`).
* `GET /api/roadmap/plan`: Loads active weekly study plan, hydrates resource links, merges session statuses, detects `skills_changed` flag, and computes weekly & overall progress %.
* `POST /api/roadmap/plan`: Generates and persists a personalized weekly study plan (AI or demo mode). Enforces weekly minute caps, strips unknown resource IDs, excludes MEDIUM/HIGH skills from new learning, carries over completed sessions upon regeneration, and applies 5 regens/day quota. Body: `{ hours_per_week, weeks, learning_style, target_date }`.
* `PUT /api/roadmap/plan/sessions/<session_key>`: Updates status of a study plan session (`pending`, `in_progress`, `completed`).

### Learning Hub & Projects (`/api`)
* `GET /api/resources`: Returns learning resources and domain practice items with completion status.
* `PUT /api/resources/<id>/complete`: Toggles resource completion flag.
* `GET /api/projects`: Returns recommended projects and milestone status.
* `PUT /api/projects/<id>/status`: Updates project status and milestones array.

### Interview Preparation & AI Mock Interview (`/api/interview`)
* `GET /api/interview/questions`: Returns question bank filtered by role, category, or difficulty. Query parameters: `role`, `category`, `difficulty`.
* `POST /api/interview/mock/start`: Initializes a mock interview session and returns masked questions. Body: `{ role: string, category: string, difficulty: string, num_questions: number, focus_missing_skills: boolean, weak_topics_only: boolean, weak_topics: string[] }`.
  - Determines mode (`openai` if API key set & quota available, else `demo`).
  - Strict role-appropriateness: non-technical tracks (Finance, HR, Marketing) never receive programming questions.
  - Returns: `{ session_id, mode, badge, questions: [{ id, role, category, difficulty, topic, skill, type, question, options }] }`.
* `POST /api/interview/mock/answer`: Evaluates student written or MCQ answer against strict rubric criteria. Body: `{ session_id: string, question_id: string, answer: string, is_retry: boolean }`.
  - Sanity check: answers under 10 words or copied questions are capped at max 20 score with explanation.
  - Prompt injection defense: treats student answer strictly as data.
  - Server calculation: computes `question_score = round(average(4 criteria) * 20)` (0-100 scale).
  - Returns: `{ is_correct, score, scores: { relevance, completeness, clarity, example_or_evidence }, what_was_good, what_was_missing, improvement_tips, better_answer, topics_to_revise, confidence_note, follow_up_question, mode, badge, notice }`.
* `POST /api/interview/mock/finish`: Finalizes mock session, calculates overall average score, criterion averages, strong topics ($\ge 75$), weak topics ($< 60$), and persists to `mock_interviews`. Body: `{ session_id: string }`.
  - Returns: `{ mock_id, score, accuracy, criterion_averages, strong_topics, weak_topics, review, badge, notice }`.
* `GET /api/interview/stats`: Returns aggregate student practice attempts, average score, and topic-wise breakdown with strict user isolation (`WHERE user_id = ?`).

### Readiness, Internships, Progress & Admin
* `GET /api/readiness`: Computes 5-pillar deterministic readiness score and AI coaching summary.
* `GET /api/internships`: Returns ranked fictional demo internships with match % and missing skills.
* `GET /api/progress`: Returns aggregate student progress across skills, tasks, and tests.
* `GET /api/admin/stats`: Returns admin aggregate statistics (admin role required).
* `POST /api/settings/reset`: Resets student activity data back to demo baseline.
* `POST /api/settings/delete-account`: Permanently purges student account and records.
* `GET /api/health`: Health status check for monitoring and hosting pings.
