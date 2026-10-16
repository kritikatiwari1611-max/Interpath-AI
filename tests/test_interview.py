import pytest
from backend.services.interview_service import get_answer_feedback, get_all_questions

def test_mcq_feedback_correct():
    """Correct MCQ selection should evaluate to True with full score."""
    q = {
        "type": "mcq",
        "correctAnswer": "list",
        "explanation": "Lists are mutable."
    }
    fb = get_answer_feedback(q, "list")
    assert fb["is_correct"] is True
    assert fb["score"] == 100
    assert "Correct!" in fb["feedback"]

def test_mcq_feedback_incorrect():
    """Incorrect MCQ selection should evaluate to False with 0 score."""
    q = {
        "type": "mcq",
        "correctAnswer": "list",
        "explanation": "Lists are mutable."
    }
    fb = get_answer_feedback(q, "tuple")
    assert fb["is_correct"] is False
    assert fb["score"] == 0

def test_written_feedback_keywords_and_example():
    """Written response covering keywords, reasonable length, and an example earns passing grade."""
    q = {
        "type": "written",
        "keywords": ["shallow", "deep", "copy", "nested", "reference"],
        "sampleAnswer": "..."
    }
    user_answer = (
        "A shallow copy creates a new collection object and populates it with references to the child objects. "
        "In contrast, a deep copy duplicates all nested objects recursively so changes don't affect the original. "
        "For example, modifying inner elements in a shallow copy changes both structures."
    )
    fb = get_answer_feedback(q, user_answer)
    assert fb["is_correct"] is True
    assert fb["score"] >= 70
    assert fb["keyword_coverage"] >= 0.8
    assert "shallow" in fb["found_keywords"]

def test_questions_change_with_role():
    """Question bank filters properly by target role."""
    all_q = get_all_questions()
    py_q = [q for q in all_q if q.get("role") == "python-developer"]
    fin_q = [q for q in all_q if q.get("role") == "finance"]

    assert len(py_q) >= 10
    assert len(fin_q) >= 10
    # Python questions shouldn't overlap with Finance topics
    py_topics = {q["topic"].lower() for q in py_q}
    fin_topics = {q["topic"].lower() for q in fin_q}
    assert "financial statements" not in py_topics
    assert "concurrency" not in fin_topics
