import json
from pathlib import Path
from backend.config import KNOWLEDGE_BASE_DIR

_INTERVIEW_QUESTIONS_CACHE = []

def get_all_questions() -> list:
    """Loads interview questions from knowledge_base/interview_questions.json."""
    global _INTERVIEW_QUESTIONS_CACHE
    if not _INTERVIEW_QUESTIONS_CACHE:
        q_path = KNOWLEDGE_BASE_DIR / "interview_questions.json"
        if q_path.exists():
            with open(q_path, "r", encoding="utf-8") as f:
                _INTERVIEW_QUESTIONS_CACHE = json.load(f)
        else:
            _INTERVIEW_QUESTIONS_CACHE = []
    return _INTERVIEW_QUESTIONS_CACHE

def get_answer_feedback(question: dict, student_answer: str) -> dict:
    """
    Evaluates a candidate's answer through rule-based evaluation.
    Label: 'Rule-based feedback, not AI evaluation.'
    In AI mode this may also supply tips, but numeric scoring remains deterministic.
    """
    q_type = question.get("type", "written")
    
    if q_type == "mcq":
        correct_ans = str(question.get("correctAnswer", "")).strip().lower()
        candidate_ans = str(student_answer).strip().lower()
        is_correct = (correct_ans == candidate_ans)
        
        feedback_text = (
            "Correct! " + question.get("explanation", "Good job.")
            if is_correct else
            f"Incorrect. The correct answer was '{question.get('correctAnswer')}'. {question.get('explanation', '')}"
        )
        return {
            "is_correct": is_correct,
            "score": 100 if is_correct else 0,
            "keyword_coverage": 1.0 if is_correct else 0.0,
            "feedback": feedback_text,
            "type": "mcq",
            "eval_label": "Rule-based feedback, not AI evaluation."
        }

    # WRITTEN / EXPLANATION QUESTION EVALUATION
    keywords = [k.lower() for k in question.get("keywords", [])]
    user_text = str(student_answer).strip()
    user_lower = user_text.lower()
    
    # 1. Keyword coverage
    found_keywords = [k for k in keywords if k in user_lower]
    keyword_coverage = (len(found_keywords) / len(keywords)) if keywords else 1.0
    
    # 2. Length check (expecting at least 15 words)
    words = user_text.split()
    word_count = len(words)
    has_reasonable_length = word_count >= 15
    
    # 3. Example check
    example_indicators = ["for example", "e.g.", "such as", "instance", "like when", "scenario"]
    has_example = any(ind in user_lower for ind in example_indicators)

    # Score calculation
    # 60% keywords + 20% length + 20% example presence
    score = (keyword_coverage * 60) + (20 if has_reasonable_length else min(20, word_count)) + (20 if has_example else 0)
    score = round(min(100, max(0, score)))
    is_acceptable = score >= 50

    critique = []
    if missing_k := [k for k in keywords if k not in found_keywords]:
        critique.append(f"Consider addressing key concepts: {', '.join(missing_k[:4])}.")
    if not has_reasonable_length:
        critique.append("Your response was very brief. Elaborate further to demonstrate deep technical understanding.")
    if not has_example:
        critique.append("Tip: Including a concrete code or project example makes your answer significantly stronger.")
        
    feedback_text = " ".join(critique) if critique else "Strong and comprehensive response with solid terminology and structure!"

    return {
        "is_correct": is_acceptable,
        "score": score,
        "keyword_coverage": round(keyword_coverage, 2),
        "found_keywords": found_keywords,
        "missing_keywords": [k for k in keywords if k not in found_keywords],
        "feedback": feedback_text,
        "type": "written",
        "eval_label": "Rule-based feedback, not AI evaluation."
    }
