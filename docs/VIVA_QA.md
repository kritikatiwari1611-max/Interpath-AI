# Questions and simple, clear answers for viva presentation examinations

1. Q: Why did you choose Flask instead of Django or FastAPI?
   A: Flask is lightweight, minimal, and transparent. It allows beginners to understand the exact lifecycle of HTTP requests and session handling without heavy ORM magic, making every line of code explainable in a viva.

2. Q: Why did you use deterministic rules alongside the AI instead of letting the AI compute readiness scores?
   A: Large Language Models (LLMs) suffer from hallucinations and non-deterministic variability (returning different numbers for the same input). An internship readiness score must be consistent, auditable, and transparent for candidates. The rules calculate the numbers, while the AI merely provides friendly textual feedback.

3. Q: How is the Skill Gap calculated?
   A: Each required skill is assigned an importance multiplier (Core = 3, Important = 2, Bonus = 1) and proficiency weights (Beginner = 0.4, Intermediate = 0.7, Advanced = 1.0, Missing = 0.0). The total earned points divided by maximum possible points gives the deterministic match percentage.

4. Q: How is the Internship Readiness Score computed?
   A: It is a weighted composite of 5 pillars: Skills (35%), Projects (25%), Resume (15%), Interview Practice (20%), and Certifications (5%). Roles like UI/UX customize this to give higher weight (35%) to Projects.

5. Q: How do you handle non-technical courses like B.Com or BBA?
   A: In roles.json, non-technical tracks like Finance or HR do not require programming skills. Instead, they evaluate domain competencies like Financial Modeling, Statement Analysis, or Talent Sourcing.

6. Q: Why can the AI never change the score?
   A: To preserve trust and academic honesty. The AI function accepts the deterministic score as an immutable input and only authors coaching tips.

7. Q: How are passwords protected?
   A: Passwords are encrypted using Werkzeug's secure generate_password_hash (salted PBKDF2 with SHA-256) before entering the database.

8. Q: How does the application prevent SQL Injection?
   A: By exclusively using parameterized queries with ? (or %s in PostgreSQL) placeholders. Raw user inputs are never concatenated into SQL strings.

9. Q: How do you prevent CSRF attacks?
   A: State-changing requests (POST/PUT/DELETE) verify an X-CSRF-Token issued during session initialization, and session cookies use SameSite=Lax and HttpOnly.

10. Q: What is the purpose of the three-dot (⋮) menu?
    A: It provides quick, accessible navigation to all 12 platform modules from the top navigation bar, featuring keyboard navigation (Escape, arrow keys) and ARIA attributes.

11. Q: What data structures did you use in Python and why?
    A: 
    - Lists for ordered stages, tasks, and questions.
    - Dicts for O(1) role lookups by ID and skill lookups.
    - Sets for fast membership checking of acquired student skills.
    - FIFO Queue logic in the service worker offline outbox.

12. Q: How does the application switch between local SQLite and PostgreSQL?
    A: Through the db.py abstraction layer. When DATABASE_URL is set, it connects via psycopg2; otherwise, it defaults to local SQLite.

13. Q: What happens if there is no internet connection or OpenAI API key?
    A: The application automatically operates in Offline Demo Mode (AI_MODE=demo). All scoring, roadmaps, questions, and matching continue to function seamlessly without external dependencies.

14. Q: How are mock interview written answers evaluated?
    A: The get_answer_feedback function evaluates keyword coverage (60%), word length (20%), and presence of concrete examples (20%), providing actionable rule-based tips.

15. Q: What does Provisional readiness status mean?
    A: If a student has an empty profile or hasn't selected a role, the system flags the score as provisional and outlines specific steps needed to complete it.

16. Q: Why do you provide fictional internship data?
    A: To maintain honesty. The app clearly labels listings as "Demo data, not live vacancies" rather than claiming real job submissions.

17. Q: How are database indexes used?
    A: Indexes are defined on user_id, role_id, and timestamps (e.g. user_skills, mock_interviews) to ensure instant query performance even with large volumes of candidate records.

18. Q: Can an Admin edit student data?
    A: No. The Admin dashboard provides strictly read-only aggregate metrics, such as student counts and role popularity.

19. Q: How is the student's progress score calculated on the Progress page?
    A: It evaluates 5 activity vectors: skills improved, roadmap tasks completed, learning resources finished, practice accuracy, and portfolio projects done.

20. Q: What is a Progressive Web App (PWA)?
    A: PWA enables web apps to feel like native apps through a manifest.json file, icons, and a Service Worker that caches static assets for offline usage.

21. Q: How does the login rate limiter work?
    A: It tracks failed attempts by client IP and email. After 5 consecutive failures, the account is temporarily locked out for 5 minutes to prevent brute-force attacks.

22. Q: What is the daily AI call limit?
    A: To prevent API abuse, each user is allotted a maximum of 30 AI calls per day, politely falling back to demo mode once the quota is reached.

23. Q: How does multi-language coaching work?
    A: The AI coaching service accepts language parameters ("en" or "hi") and provides advice in English or friendly Hinglish/Hindi.

24. Q: What are the current limitations of the system?
    A: It relies on self-reported skill levels rather than automated code execution sandboxes, and internship listings are demonstrative.

25. Q: What is the roadmap for future enhancements?
    A: Future phases can integrate automated PDF resume parsing with NLP, live job board APIs, and machine learning for collaborative filtering recommendations.
