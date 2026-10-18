import json
import time
import random
from pathlib import Path
from backend.config import KNOWLEDGE_BASE_DIR
from backend.db import execute_query
from backend.services import ai_service

_INTERVIEW_QUESTIONS_CACHE = []

# In-memory dictionary tracking active mock interview sessions:
# { session_id: { "user_id": int, "role_id": str, "mode": str, "questions": list, "answers": list, ... } }
_MOCK_SESSIONS = {}

# Self-harm & crisis keywords to protect student safety
SAFETY_CRISIS_KEYWORDS = {
    "kill myself", "suicide", "want to die", "end my life", 
    "hurt myself", "self harm", "cutting myself", "commit suicide"
}

def get_all_questions() -> list:
    """Loads interview questions from knowledge_base/interview_questions.json."""
    global _INTERVIEW_QUESTIONS_CACHE
    q_path = KNOWLEDGE_BASE_DIR / "interview_questions.json"
    if q_path.exists():
        with open(q_path, "r", encoding="utf-8") as f:
            _INTERVIEW_QUESTIONS_CACHE = json.load(f)
    else:
        _INTERVIEW_QUESTIONS_CACHE = []
    return _INTERVIEW_QUESTIONS_CACHE


def evaluate_written_rule_based(question: dict, student_answer: str, sanity_violation: str = None) -> dict:
    """
    Evaluates written answer deterministically using keyword coverage, structure, and examples.
    Used in Demo Mode or as fallback when AI is unavailable.
    """
    keywords = [k.lower() for k in question.get("keywords", [])]
    user_text = str(student_answer).strip()
    user_lower = user_text.lower()
    words = user_text.split()
    word_count = len(words)

    # 1. Keyword matching
    found_keywords = [k for k in keywords if k in user_lower]
    missing_keywords = [k for k in keywords if k not in found_keywords]
    keyword_cov = (len(found_keywords) / len(keywords)) if keywords else 1.0

    # 2. Example check (looking for concrete phrasing)
    example_indicators = ["for example", "e.g.", "such as", "for instance", "in my project", "scenario", "in my experience"]
    has_example = any(ind in user_lower for ind in example_indicators)

    # 3. Calculate 4 rubric criteria (0.0 to 5.0 scale)
    relevance = min(5.0, round(keyword_cov * 5.0, 1))
    completeness = min(5.0, round((keyword_cov * 3.0) + (2.0 if word_count >= 30 else (word_count / 15.0)), 1))
    clarity = 5.0 if (word_count >= 20 and any(p in user_text for p in ['.', '!', '?'])) else (3.0 if word_count >= 10 else 1.0)
    example_score = 5.0 if has_example else (2.0 if word_count >= 35 else 1.0)

    # Sanity check: cap at 20 if <10 words or repeated question
    if sanity_violation:
        relevance = min(1.0, relevance)
        completeness = min(1.0, completeness)
        clarity = min(1.0, clarity)
        example_score = min(1.0, example_score)

    # Server calculates totals: avg(criteria) * 20
    avg_criterion = (relevance + completeness + clarity + example_score) / 4.0
    question_score = round(avg_criterion * 20)
    if sanity_violation:
        question_score = min(20, question_score)

    # Construct helpful feedback lists
    what_was_good = []
    if found_keywords:
        what_was_good.append(f"Addressed key concepts: {', '.join(found_keywords[:4])}.")
    if has_example:
        what_was_good.append("Included practical example / application context.")
    if not what_was_good and word_count >= 10:
        what_was_good.append("Attempted the question with structured effort.")

    what_was_missing = []
    if sanity_violation:
        what_was_missing.append(sanity_violation)
    elif missing_keywords:
        what_was_missing.append(f"Key concepts missing: {', '.join(missing_keywords[:4])}.")
    if word_count < 25 and not sanity_violation:
        what_was_missing.append("Response is brief; expanding with more depth will show technical mastery.")

    improvement_tips = []
    if not has_example:
        improvement_tips.append("Add a concrete example or project use case to make your explanation compelling.")
    if missing_keywords:
        improvement_tips.append(f"Incorporate industry terms like {', '.join(missing_keywords[:2])} in your answer.")
    if not improvement_tips:
        improvement_tips.append("Keep practicing concise, structured delivery under time pressure.")

    return {
        "is_correct": question_score >= 60,
        "score": question_score,
        "keyword_coverage": round(keyword_cov, 2),
        "found_keywords": found_keywords,
        "missing_keywords": missing_keywords,
        "scores": {
            "relevance": relevance,
            "completeness": completeness,
            "clarity": clarity,
            "example_or_evidence": example_score
        },
        "what_was_good": what_was_good,
        "what_was_missing": what_was_missing,
        "improvement_tips": improvement_tips,
        "better_answer": question.get("sampleAnswer", "Review standard industry documentation for this concept."),
        "topics_to_revise": [question.get("topic", "General Revision")],
        "confidence_note": "Rule-based evaluation based on keyword coverage and structure.",
        "follow_up_question": "",
        "type": "written",
        "mode": "demo",
        "badge": "Demo mode (rule-based)",
        "notice": "AI feedback is a practice aid and can make mistakes. It is not a hiring decision."
    }


def get_answer_feedback(question: dict, student_answer: str, role: str = "python-developer", mode: str = "demo", student_info: dict = None) -> dict:
    """
    Unified evaluation function for interview answers.
    Evaluates MCQs deterministically.
    For written questions: validates safety, applies sanity checks, and routes to AI or Demo mode.
    The server, not the AI, calculates the final numeric scores.
    """
    user_text = str(student_answer).strip()
    user_lower = user_text.lower()
    q_type = question.get("type", "written")

    # 1. Safety / Self-harm check
    if any(crisis_word in user_lower for crisis_word in SAFETY_CRISIS_KEYWORDS):
        return {
            "is_correct": False,
            "score": 0,
            "scores": {"relevance": 0.0, "completeness": 0.0, "clarity": 0.0, "example_or_evidence": 0.0},
            "what_was_good": [],
            "what_was_missing": ["Evaluation suspended for safety."],
            "improvement_tips": ["If you are feeling overwhelmed or distressed, please connect with support services (e.g., call or text 988 or reach out to someone you trust). You matter."],
            "better_answer": "",
            "topics_to_revise": [],
            "confidence_note": "Safety filter activated.",
            "follow_up_question": "",
            "type": q_type,
            "mode": mode,
            "badge": "Safety Notice",
            "notice": "Your health and well-being come first."
        }

    # 2. MCQ Evaluation (Always deterministic and rule-based)
    if q_type == "mcq":
        correct_ans = str(question.get("correctAnswer", "")).strip().lower()
        candidate_ans = user_text.lower()
        is_correct = (correct_ans == candidate_ans)
        
        explanation = question.get("explanation", "")
        feedback_text = (
            f"Correct! {explanation}" if is_correct 
            else f"Incorrect. The correct answer was '{question.get('correctAnswer')}'. {explanation}"
        )
        
        score = 100 if is_correct else 0
        criterion_score = 5.0 if is_correct else 0.0

        return {
            "is_correct": is_correct,
            "score": score,
            "scores": {
                "relevance": criterion_score,
                "completeness": criterion_score,
                "clarity": criterion_score,
                "example_or_evidence": criterion_score
            },
            "what_was_good": ["Selected the correct option."] if is_correct else [],
            "what_was_missing": [] if is_correct else [f"Selected wrong option. Correct was '{question.get('correctAnswer')}'."],
            "improvement_tips": ["Review core concepts before continuing."] if not is_correct else ["Great recall! Keep this momentum."],
            "better_answer": question.get("explanation", question.get("correctAnswer", "")),
            "topics_to_revise": [] if is_correct else [question.get("topic", "Core Knowledge")],
            "confidence_note": "Deterministic MCQ validation.",
            "follow_up_question": "",
            "feedback": feedback_text,
            "type": "mcq",
            "mode": "demo",
            "badge": "Demo mode (rule-based)",
            "notice": "AI feedback is a practice aid and can make mistakes. It is not a hiring decision."
        }

    # 3. Rule-based sanity checks for written answers
    words = user_text.split()
    word_count = len(words)
    sanity_violation = None

    if word_count == 0:
        sanity_violation = "Answer was empty. Please provide an explanation."
    elif word_count < 10:
        sanity_violation = "Your answer was very short (under 10 words). Provide a structured explanation to demonstrate your understanding."
    else:
        # Check if the student merely repeated or copied the question
        q_words = set(question.get("question", "").lower().split())
        a_words = set(user_lower.split())
        if len(q_words) > 3 and len(a_words.intersection(q_words)) / len(a_words) > 0.85:
            sanity_violation = "The response appears to copy or repeat the question rather than answering it."

    # 4. AI Evaluation Mode
    if mode == "openai":
        course = (student_info or {}).get("course", "Bachelor of Technology")
        difficulty = question.get("difficulty", "Intermediate")
        lang = (student_info or {}).get("language", "en")

        ai_result = ai_service.call_ai_evaluation(
            role=role,
            question=question.get("question", ""),
            answer=user_text,
            course=course,
            difficulty=difficulty,
            student_lang=lang
        )

        if ai_result and "scores" in ai_result:
            sc = ai_result["scores"]
            # Validate and clamp criteria between 0.0 and 5.0
            relevance = min(5.0, max(0.0, float(sc.get("relevance", 3.0))))
            completeness = min(5.0, max(0.0, float(sc.get("completeness", 3.0))))
            clarity = min(5.0, max(0.0, float(sc.get("clarity", 3.0))))
            example_score = min(5.0, max(0.0, float(sc.get("example_or_evidence", 3.0))))

            # Enforce sanity caps: if answer failed sanity check, cap scores at <= 1.0 (max 20 total)
            if sanity_violation:
                relevance = min(1.0, relevance)
                completeness = min(1.0, completeness)
                clarity = min(1.0, clarity)
                example_score = min(1.0, example_score)

            # Server calculates the totals: average of criteria * 20
            avg_criterion = (relevance + completeness + clarity + example_score) / 4.0
            question_score = round(avg_criterion * 20)
            if sanity_violation:
                question_score = min(20, question_score)

            what_missing = ai_result.get("what_was_missing", [])
            if sanity_violation and sanity_violation not in what_missing:
                what_missing.insert(0, sanity_violation)

            return {
                "is_correct": question_score >= 60,
                "score": question_score,
                "keyword_coverage": round(relevance / 5.0, 2),
                "scores": {
                    "relevance": round(relevance, 1),
                    "completeness": round(completeness, 1),
                    "clarity": round(clarity, 1),
                    "example_or_evidence": round(example_score, 1)
                },
                "what_was_good": ai_result.get("what_was_good", [])[:3],
                "what_was_missing": what_missing[:3],
                "improvement_tips": ai_result.get("improvement_tips", [])[:3],
                "better_answer": ai_result.get("better_answer", "")[:900] or question.get("sampleAnswer", ""),
                "topics_to_revise": ai_result.get("topics_to_revise", [question.get("topic", role)])[:2],
                "confidence_note": ai_result.get("confidence_note", "Evaluated against role standards."),
                "follow_up_question": ai_result.get("follow_up_question", ""),
                "type": "written",
                "mode": "openai",
                "badge": "AI mode",
                "notice": "AI feedback is a practice aid and can make mistakes. It is not a hiring decision."
            }

    # 5. Demo Mode / Fallback (Offline, reliable rule-based evaluation)
    return evaluate_written_rule_based(question, user_text, sanity_violation)


# -------------------------------------------------------------
# SESSION LIFECYCLE MANAGEMENT FOR MOCK INTERVIEWS
# -------------------------------------------------------------

def create_mock_session(user_id: int, role_id: str, category: str, difficulty: str, num_questions: int, focus_missing_skills: bool = False, weak_topics_only: bool = False, target_weak_topics: list = None) -> dict:
    """
    Initializes a new mock interview session.
    Honors role-appropriateness (no coding questions for non-tech roles).
    Generates masked questions sent to the client.
    """
    can_use_ai, _ = ai_service.is_ai_available(user_id)
    mode = "openai" if can_use_ai else "demo"

    all_q = get_all_questions()

    # Non-technical tracks must never encounter programming questions
    NON_TECH_ROLES = {"finance", "human-resources", "digital-marketing", "business-analyst"}
    is_non_tech = role_id in NON_TECH_ROLES

    # Filter candidate questions from knowledge base
    candidates = []
    for q in all_q:
        q_role = q.get("role")
        # Ensure role match or generic
        if q_role != role_id and q_role != "all":
            continue
        # Strict exclusion of coding questions if non-tech role
        if is_non_tech and q.get("category") == "Technical" and any(code_k in str(q).lower() for code_k in ["def ", "class ", "function()", "import "]):
            continue
        # Filter by category
        if category != "all" and q.get("category", "").lower() != category.lower():
            continue
        # Filter by difficulty
        if difficulty != "all" and q.get("difficulty", "").lower() != difficulty.lower():
            continue
        candidates.append(q)

    # If practicing weak topics, filter specifically by those topics
    if weak_topics_only and target_weak_topics:
        weak_set = {t.lower() for t in target_weak_topics}
        topic_filtered = [q for q in candidates if q.get("topic", "").lower() in weak_set]
        if topic_filtered:
            candidates = topic_filtered

    # If focus on missing skills requested, prioritize user's missing/low skills
    if focus_missing_skills and user_id:
        user_skills = execute_query(
            "SELECT skill_name FROM skills WHERE user_id = ? AND (status = 'Missing' OR level = 'Low')",
            (user_id,),
            fetch_all=True
        )
        if user_skills:
            missing_names = {s["skill_name"].lower() for s in user_skills}
            prioritized = [q for q in candidates if q.get("skill", "").lower() in missing_names]
            if prioritized:
                # Place prioritized questions first
                remaining = [q for q in candidates if q not in prioritized]
                candidates = prioritized + remaining

    if not candidates:
        candidates = all_q

    # Pick desired count
    sample_pool = list(candidates)
    random.shuffle(sample_pool)
    selected = sample_pool[:min(num_questions, len(sample_pool))]

    session_id = f"mock_{user_id}_{int(time.time() * 1000)}"

    _MOCK_SESSIONS[session_id] = {
        "session_id": session_id,
        "user_id": user_id,
        "role_id": role_id,
        "mode": mode,
        "questions": selected,
        "answers": [],
        "created_at": time.time(),
        "completed": False
    }

    # Mask answers/keys so candidate cannot view answers in dev tools
    masked = []
    for q in selected:
        masked.append({
            "id": q["id"],
            "role": q.get("role"),
            "category": q.get("category"),
            "difficulty": q.get("difficulty"),
            "topic": q.get("topic"),
            "skill": q.get("skill"),
            "type": q.get("type"),
            "question": q.get("question"),
            "options": q.get("options", [])
        })

    badge = "AI mode" if mode == "openai" else "Demo mode (rule-based)"

    return {
        "session_id": session_id,
        "mode": mode,
        "badge": badge,
        "questions": masked,
        "total": len(masked)
    }


def get_mock_session(session_id: str, user_id: int) -> dict | None:
    """Retrieves an active mock session verifying student ownership."""
    sess = _MOCK_SESSIONS.get(session_id)
    if sess and sess["user_id"] == user_id:
        return sess
    return None


def record_session_answer(session_id: str, user_id: int, question_id: str, student_answer: str, is_retry: bool = False) -> dict | None:
    """
    Evaluates an answer within an active session, persists the attempt in SQLite,
    and returns comprehensive rubric feedback.
    """
    sess = get_mock_session(session_id, user_id)
    if not sess:
        return None

    # Find the question in session
    question = next((q for q in sess["questions"] if q["id"] == question_id), None)
    if not question:
        return None

    # Fetch student degree info for personalized AI prompt
    try:
        user_row = execute_query(
            "SELECT degree_branch FROM student_profiles WHERE user_id = ?",
            (user_id,),
            fetch_one=True
        )
        course_name = user_row["degree_branch"] if user_row and user_row.get("degree_branch") else "Undergraduate"
    except Exception:
        course_name = "Undergraduate"

    student_info = {
        "course": course_name,
        "language": "en"
    }

    # If in AI mode, ensure user hasn't exceeded 30 daily calls
    mode = sess["mode"]
    if mode == "openai":
        allowed = ai_service.check_and_increment_quota(user_id)
        if not allowed:
            mode = "demo"
            sess["mode"] = "demo"

    feedback = get_answer_feedback(
        question=question,
        student_answer=student_answer,
        role=sess["role_id"],
        mode=mode,
        student_info=student_info
    )

    # Record into session state
    entry = {
        "question_id": question_id,
        "question_text": question.get("question", ""),
        "student_answer": student_answer,
        "topic": question.get("topic", "General"),
        "skill": question.get("skill", ""),
        "type": question.get("type", "written"),
        "score": feedback["score"],
        "scores": feedback["scores"],
        "is_correct": feedback["is_correct"],
        "feedback": feedback,
        "is_retry": is_retry
    }

    # If it's a retry of the same question, replace previous entry
    existing_idx = next((i for i, a in enumerate(sess["answers"]) if a["question_id"] == question_id), None)
    if existing_idx is not None and is_retry:
        sess["answers"][existing_idx] = entry
    else:
        sess["answers"].append(entry)

    # Persist attempt into database table
    try:
        execute_query(
            """INSERT INTO interview_attempts 
               (user_id, question_id, role_id, topic, answer, is_correct, keyword_coverage, score, mode, feedback_json) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                question_id,
                sess["role_id"],
                question.get("topic", "General"),
                student_answer,
                1 if feedback["is_correct"] else 0,
                feedback["scores"].get("relevance", 0.0) / 5.0,
                feedback["score"],
                mode,
                json.dumps(feedback)
            ),
            commit=True
        )
    except Exception as e:
        print(f"Failed to record attempt in DB: {e}")

    return feedback


def finish_mock_session(session_id: str, user_id: int) -> dict | None:
    """
    Computes overall practice score, 4-criterion averages, strongest and weak topics,
    and records the completed session in SQLite.
    """
    sess = get_mock_session(session_id, user_id)
    if not sess:
        return None

    answers = sess["answers"]
    total = len(answers)
    if total == 0:
        return {"score": 0, "accuracy": 0, "weak_topics": [], "strong_topics": [], "review": []}

    # Server calculates overall practice score = average of question scores
    question_scores = [a["score"] for a in answers]
    overall_score = round(sum(question_scores) / total)

    correct_count = sum(1 for a in answers if a["is_correct"])
    accuracy = round((correct_count / total) * 100, 1)

    # 4 Criterion Averages
    criterion_sums = {"relevance": 0.0, "completeness": 0.0, "clarity": 0.0, "example_or_evidence": 0.0}
    for a in answers:
        sc = a.get("scores", {})
        for k in criterion_sums:
            criterion_sums[k] += float(sc.get(k, 0.0))

    criterion_averages = {k: round(v / total, 1) for k, v in criterion_sums.items()}

    # Categorize Strongest topics (>= 75 score) and Weak topics (< 60 or incorrect MCQ)
    strong_topics = []
    weak_topics = []
    topic_scores = {}

    for a in answers:
        top = a["topic"]
        if top not in topic_scores:
            topic_scores[top] = []
        topic_scores[top].append(a["score"])

    for top, scores_list in topic_scores.items():
        avg_top = sum(scores_list) / len(scores_list)
        if avg_top >= 75:
            strong_topics.append(top)
        elif avg_top < 60:
            weak_topics.append(top)

    # Per-question review package
    review = []
    for a in answers:
        fb = a["feedback"]
        review.append({
            "question_id": a["question_id"],
            "question": a["question_text"],
            "topic": a["topic"],
            "student_answer": a["student_answer"],
            "score": a["score"],
            "scores": a["scores"],
            "what_was_good": fb.get("what_was_good", []),
            "what_was_missing": fb.get("what_was_missing", []),
            "improvement_tips": fb.get("improvement_tips", []),
            "better_answer": fb.get("better_answer", ""),
            "confidence_note": fb.get("confidence_note", "")
        })

    # Save completed mock into database
    mock_id = execute_query(
        """INSERT INTO mock_interviews 
           (user_id, role_id, score, accuracy, weak_topics, mode, session_id, details_json, topic_results) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            user_id,
            sess["role_id"],
            overall_score,
            accuracy,
            json.dumps(weak_topics),
            sess["mode"],
            session_id,
            json.dumps(review),
            json.dumps(topic_scores)
        ),
        commit=True
    )

    sess["completed"] = True

    return {
        "mock_id": mock_id,
        "score": overall_score,
        "accuracy": accuracy,
        "criterion_averages": criterion_averages,
        "strong_topics": strong_topics,
        "weak_topics": weak_topics,
        "review": review,
        "badge": "AI mode" if sess["mode"] == "openai" else "Demo mode (rule-based)",
        "notice": "AI feedback is a practice aid and can make mistakes. It is not a hiring decision."
    }
