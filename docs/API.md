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

### Roles & Roadmap (`/api`)
* `GET /api/roles`: Returns all 12+ roles from the knowledge base.
* `GET /api/roles/<role_id>`: Returns details and prerequisites of a single role.
* `GET /api/roadmap`: Generates the personalized 4-stage roadmap based on student gaps.
* `PUT /api/roadmap/tasks/<task_key>`: Updates task status (`pending`, `in_progress`, `completed`).

### Learning Hub & Projects (`/api`)
* `GET /api/resources`: Returns learning resources and domain practice items with completion status.
* `PUT /api/resources/<id>/complete`: Toggles resource completion flag.
* `GET /api/projects`: Returns recommended projects and milestone status.
* `PUT /api/projects/<id>/status`: Updates project status and milestones array.

### Interview Preparation (`/api/interview`)
* `GET /api/interview/questions`: Returns question bank filtered by role, category, or difficulty.
* `POST /api/interview/mock/start`: Initializes a mock interview session and returns masked questions.
* `POST /api/interview/mock/answer`: Evaluates candidate answer via rule-based keyword logic.
* `POST /api/interview/mock/finish`: Records mock interview session score, accuracy, and weak topics.
* `GET /api/interview/stats`: Returns aggregate student practice attempts and topic-wise accuracy.

### Readiness, Internships, Progress & Admin
* `GET /api/readiness`: Computes 5-pillar deterministic readiness score and AI coaching summary.
* `GET /api/internships`: Returns ranked fictional demo internships with match % and missing skills.
* `GET /api/progress`: Returns aggregate student progress across skills, tasks, and tests.
* `GET /api/admin/stats`: Returns admin aggregate statistics (admin role required).
* `POST /api/settings/reset`: Resets student activity data back to demo baseline.
* `POST /api/settings/delete-account`: Permanently purges student account and records.
* `GET /api/health`: Health status check for monitoring and hosting pings.
