import pytest
from datetime import datetime, timedelta
from backend.services.ai_service import check_and_increment_quota, generate_ai_summary
from backend.routes.auth import is_locked_out, record_failed_attempt, reset_failed_attempts
from backend.config import LOGIN_RATE_LIMIT, AI_DAILY_LIMIT

def test_login_rate_limiting_lockout():
    """5 consecutive failed attempts must lock out the account."""
    test_key = "test_ip_rate_limit"
    reset_failed_attempts(test_key)
    
    for _ in range(LOGIN_RATE_LIMIT - 1):
        record_failed_attempt(test_key)
        assert is_locked_out(test_key) is False

    # 5th failed attempt triggers lockout
    record_failed_attempt(test_key)
    assert is_locked_out(test_key) is True
    
    # Cleanup
    reset_failed_attempts(test_key)
    assert is_locked_out(test_key) is False

def test_ai_daily_limit_quota():
    """Users cannot exceed 30 AI calls per day."""
    user_id = 9999
    # Consume 30 calls
    for i in range(AI_DAILY_LIMIT):
        assert check_and_increment_quota(user_id) is True

    # 31st call must be denied
    assert check_and_increment_quota(user_id) is False

def test_hindi_hinglish_ai_summary():
    """AI tips in Hindi/Hinglish mode return proper Hindi text guidance."""
    res = generate_ai_summary("Python Developer", 75, [], language="hi")
    assert res["mode"] == "demo"
    assert "तैयारी" in res["summary"] or "तैयारी" in res["improvement_tip"]
