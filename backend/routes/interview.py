import json
import random
from flask import Blueprint, request, jsonify, session
from backend.db import execute_query
from backend.auth_utils import login_required
from backend.services.interview_service import get_all_questions, get_answer_feedback

interview_bp = Blueprint("interview", __name__)

@interview_bp.route("/interview/questions", methods=["GET"])
@login_required
def list_questions():
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
    data = request.get_json() or {}
    role_id = data.get("role", "python-developer")
    category = data.get("category", "all")
    difficulty = data.get("difficulty", "all")
    num_questions = int(data.get("num_questions", 5))

    all_q = get_all_questions()
    candidates = [q for q in all_q if q.get("role") == role_id or q.get("role") == "all"]
    
    if category != "all":
        candidates = [q for q in candidates if q.get("category", "").lower() == category.lower()]
    if difficulty != "all":
        candidates = [q for q in candidates if q.get("difficulty", "").lower() == difficulty.lower()]

    if not candidates:
        candidates = all_q

    # Shuffle and pick num_questions
    sample_pool = list(candidates)
    random.shuffle(sample_pool)
    selected = sample_pool[:min(num_questions, len(sample_pool))]

    # Mask answers during active mock test
    masked = []
    for q in selected:
        item = {
            "id": q["id"],
            "role": q.get("role"),
            "category": q.get("category"),
            "difficulty": q.get("difficulty"),
            "topic": q.get("topic"),
            "skill": q.get("skill"),
            "type": q.get("type"),
            "question": q.get("question"),
            "options": q.get("options", [])
        }
        masked.append(item)

    return jsonify({"ok": True, "data": {"questions": masked, "total": len(masked)}})

@interview_bp.route("/interview/mock/answer", methods=["POST"])
@login_required
def evaluate_mock_answer():
    user_id = session["user_id"]
    data = request.get_json() or {}
    q_id = data.get("question_id")
    answer = data.get("answer", "")
    role_id = data.get("role_id", "python-developer")

    all_q = get_all_questions()
    question = next((q for q in all_q if q["id"] == q_id), None)
    if not question:
        return jsonify({"ok": False, "error": "Question not found"}), 404

    feedback = get_answer_feedback(question, answer)
    
    # Save attempt into database
    execute_query(
        """INSERT INTO interview_attempts 
           (user_id, question_id, role_id, topic, answer, is_correct, keyword_coverage) 
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, q_id, role_id, question.get("topic", "General"), answer, 1 if feedback["is_correct"] else 0, feedback["keyword_coverage"]),
        commit=True
    )

    return jsonify({"ok": True, "data": feedback})

@interview_bp.route("/interview/mock/finish", methods=["POST"])
@login_required
def finish_mock():
    user_id = session["user_id"]
    data = request.get_json() or {}
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
    user_id = session["user_id"]

    attempts = execute_query(
        "SELECT id, is_correct, topic, created_at FROM interview_attempts WHERE user_id = ?",
        (user_id,),
        fetch_all=True
    )
    mocks = execute_query(
        "SELECT id, role_id, score, accuracy, weak_topics, created_at FROM mock_interviews WHERE user_id = ? ORDER BY created_at DESC",
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
            topic_summary[t] = {"total": 0, "correct": 0}
        topic_summary[t]["total"] += 1
        if a["is_correct"] == 1:
            topic_summary[t]["correct"] += 1

    return jsonify({
        "ok": True,
        "data": {
            "total_attempts": total_attempts,
            "correct_count": correct_count,
            "accuracy": accuracy,
            "mock_interviews_done": len(mocks),
            "topic_summary": topic_summary,
            "recent_mocks": mocks[:5]
        }
    })
