import json
import random
from flask import Blueprint, request, jsonify, session
from backend.db import execute_query
from backend.auth_utils import login_required
from backend.services.interview_service import (
    get_all_questions,
    get_answer_feedback,
    create_mock_session,
    record_session_answer,
    finish_mock_session
)

interview_bp = Blueprint("interview", __name__)

@interview_bp.route("/interview/questions", methods=["GET"])
@login_required
def list_questions():
    """Returns curated interview questions from knowledge base with role/category filters."""
    questions = get_all_questions()
    role = request.args.get("role")
    category = request.args.get("category")
    difficulty = request.args.get("difficulty")

    filtered = questions
    if role and role != "all":
        filtered = [q for q in filtered if q.get("role") == role or q.get("role") == "all"]
    if category and category != "all":
        filtered = [q for q in filtered if q.get("category", "").lower() == category.lower()]
    if difficulty and difficulty != "all":
        filtered = [q for q in filtered if q.get("difficulty", "").lower() == difficulty.lower()]

    return jsonify({"ok": True, "data": filtered})


@interview_bp.route("/interview/mock/start", methods=["POST"])
@login_required
def start_mock():
    """
    Starts a new interactive mock interview session.
    Honors role-specific questions and supports focusing on missing skills or weak topics.
    """
    user_id = session["user_id"]
    data = request.get_json() or {}

    role_id = data.get("role", "python-developer")
    category = data.get("category", "all")
    difficulty = data.get("difficulty", "all")
    num_questions = int(data.get("num_questions", 5))
    focus_missing = bool(data.get("focus_missing_skills", False))
    weak_topics_only = bool(data.get("weak_topics_only", False))
    target_weak_topics = data.get("weak_topics", [])

    mock_sess = create_mock_session(
        user_id=user_id,
        role_id=role_id,
        category=category,
        difficulty=difficulty,
        num_questions=num_questions,
        focus_missing_skills=focus_missing,
        weak_topics_only=weak_topics_only,
        target_weak_topics=target_weak_topics
    )

    return jsonify({"ok": True, "data": mock_sess})


@interview_bp.route("/interview/mock/answer", methods=["POST"])
@login_required
def evaluate_mock_answer():
    """
    Evaluates candidate's written or MCQ answer.
    Supports session tracking with retry capability and persists the attempt per student.
    """
    user_id = session["user_id"]
    data = request.get_json() or {}

    session_id = data.get("session_id")
    q_id = data.get("question_id")
    answer = data.get("answer", "")
    is_retry = bool(data.get("is_retry", False))

    # If session_id provided, evaluate inside active mock session
    if session_id:
        feedback = record_session_answer(
            session_id=session_id,
            user_id=user_id,
            question_id=q_id,
            student_answer=answer,
            is_retry=is_retry
        )
        if not feedback:
            return jsonify({"ok": False, "error": "Active session or question not found"}), 404
        return jsonify({"ok": True, "data": feedback})

    # Direct fallback mode without session_id (e.g., question bank practice)
    role_id = data.get("role_id", "python-developer")
    all_q = get_all_questions()
    question = next((q for q in all_q if q["id"] == q_id), None)
    if not question:
        return jsonify({"ok": False, "error": "Question not found"}), 404

    feedback = get_answer_feedback(question=question, student_answer=answer, role=role_id, mode="demo")

    execute_query(
        """INSERT INTO interview_attempts 
           (user_id, question_id, role_id, topic, answer, is_correct, keyword_coverage, score, mode, feedback_json) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            user_id,
            q_id,
            role_id,
            question.get("topic", "General"),
            answer,
            1 if feedback["is_correct"] else 0,
            feedback["scores"].get("relevance", 0.0) / 5.0,
            feedback["score"],
            "demo",
            json.dumps(feedback)
        ),
        commit=True
    )

    return jsonify({"ok": True, "data": feedback})


@interview_bp.route("/interview/mock/finish", methods=["POST"])
@login_required
def finish_mock():
    """
    Finalizes the mock interview, calculates total scores, and persists results.
    """
    user_id = session["user_id"]
    data = request.get_json() or {}
    session_id = data.get("session_id")

    if session_id:
        result = finish_mock_session(session_id=session_id, user_id=user_id)
        if not result:
            return jsonify({"ok": False, "error": "Mock session not found"}), 404
        return jsonify({"ok": True, "data": result})

    # Legacy fallback calculation
    role_id = data.get("role_id", "python-developer")
    score = int(data.get("score", 0))
    accuracy = float(data.get("accuracy", 0.0))
    weak_topics = json.dumps(data.get("weak_topics", []))

    mock_id = execute_query(
        """INSERT INTO mock_interviews (user_id, role_id, score, accuracy, weak_topics) 
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, role_id, score, accuracy, weak_topics),
        commit=True
    )

    return jsonify({"ok": True, "data": {"mock_id": mock_id, "score": score, "accuracy": accuracy}})


@interview_bp.route("/interview/stats", methods=["GET"])
@login_required
def get_stats():
    """
    Retrieves student's interview stats with strict user isolation (WHERE user_id = ?).
    """
    user_id = session["user_id"]

    attempts = execute_query(
        "SELECT id, is_correct, topic, score, created_at FROM interview_attempts WHERE user_id = ?",
        (user_id,),
        fetch_all=True
    )
    mocks = execute_query(
        "SELECT id, role_id, score, accuracy, weak_topics, mode, created_at FROM mock_interviews WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
        fetch_all=True
    )

    total_attempts = len(attempts)
    correct_count = sum(1 for a in attempts if a["is_correct"] == 1)
    accuracy = round((correct_count / total_attempts * 100), 1) if total_attempts > 0 else 0.0

    # Topic-wise summary
    topic_summary = {}
    for a in attempts:
        t = a["topic"]
        if t not in topic_summary:
            topic_summary[t] = {"total": 0, "correct": 0, "scores": []}
        topic_summary[t]["total"] += 1
        if a["is_correct"] == 1:
            topic_summary[t]["correct"] += 1
        if a.get("score") is not None:
            topic_summary[t]["scores"].append(a["score"])

    # Compute topic averages
    topic_clean = {}
    for t, vals in topic_summary.items():
        avg_score = round(sum(vals["scores"]) / len(vals["scores"])) if vals["scores"] else 0
        topic_clean[t] = {
            "total": vals["total"],
            "correct": vals["correct"],
            "avg_score": avg_score
        }

    return jsonify({
        "ok": True,
        "data": {
            "total_attempts": total_attempts,
            "correct_count": correct_count,
            "accuracy": accuracy,
            "mock_interviews_done": len(mocks),
            "topic_summary": topic_clean,
            "recent_mocks": mocks[:5]
        }
    })
