import os
import json
from datetime import datetime, date
from backend.config import AI_MODE, OPENAI_API_KEY, OPENAI_MODEL, AI_DAILY_LIMIT

# In-memory dictionary tracking daily AI calls per user: { (user_id, date_str): count }
_DAILY_AI_USAGE = {}

def check_and_increment_quota(user_id: int) -> bool:
    """Enforces 30 AI calls per user per day limit. Returns True if allowed."""
    today = date.today().isoformat()
    key = (user_id, today)
    current_calls = _DAILY_AI_USAGE.get(key, 0)
    if current_calls >= AI_DAILY_LIMIT:
        return False
    _DAILY_AI_USAGE[key] = current_calls + 1
    return True

def generate_ai_summary(role_title: str, readiness_score: int, skills: list, language: str = "en") -> dict:
    """
    Generates a helpful, constructive summary and encouragement tips.
    The AI NEVER computes or alters the readiness score or match percentage numbers.
    Gracefully falls back to offline rule-based templates if API key is absent or quota met.
    """
    is_hindi = language.lower() in ["hi", "hindi", "hinglish"]
    
    # Check if OpenAI is enabled and key exists
    use_openai = (AI_MODE == "openai" and bool(OPENAI_API_KEY))
    
    if not use_openai:
        # Rule-based fallback summary
        if is_hindi:
            if readiness_score >= 70:
                summary = f"बहुत बढ़िया! आपकी {role_title} पद के लिए तैयारी {readiness_score}% है। आप सीधे इंटर्नशिप के लिए आवेदन करने के योग्य हैं।"
                tip = "अपने प्रोजेक्ट्स को GitHub/पोर्टफोलियो पर साफ तरीके से प्रदर्शित करें और इंटरव्यू की रीविजन जारी रखें।"
            elif readiness_score >= 40:
                summary = f"आपकी {role_title} के लिए तैयारी {readiness_score}% पर एक अच्छी शुरुआत है।"
                tip = "Learning Hub में अपने कोर स्किल्स को मजबूत करें और एक नया प्रैक्टिकल प्रोजेक्ट पूरा करें।"
            else:
                summary = f"आपकी तैयारी अभी शुरुआती चरण ({readiness_score}%) में है। घबराएं नहीं, रोडमैप का पालन करें।"
                tip = "रोडमैप के स्टेज 1 के बुनियादी कॉन्सेप्ट्स से शुरुआत करें और दैनिक 1 घंटा अभ्यास करें।"
        else:
            if readiness_score >= 70:
                summary = f"Excellent work! Your readiness for {role_title} is strong at {readiness_score}%. You have covered key foundational and portfolio requirements."
                tip = "Highlight your completed projects in your resume and continue targeted mock interview drills."
            elif readiness_score >= 40:
                summary = f"Good foundational progress! Your current readiness for {role_title} is {readiness_score}%. You have solid groundwork with clear room for growth."
                tip = "Prioritize the core missing skills flagged in your Skill Gap analysis and complete a milestone-driven project."
            else:
                summary = f"Your career journey for {role_title} is just getting started ({readiness_score}%). Follow the personalized roadmap step-by-step."
                tip = "Start with Stage 1 Foundation tasks. Consistent 45-minute daily practice will rapidly boost your score."

        return {
            "mode": "demo",
            "badge": "Offline Rule-based Mode",
            "summary": summary,
            "improvement_tip": tip
        }

    # If OpenAI API is configured
    try:
        import urllib.request
        prompt = (
            f"You are a mentor on InternPath AI. The student is preparing for '{role_title}'. "
            f"Their deterministic readiness score is {readiness_score}%. "
            f"Provide a 2-sentence encouraging summary and 1 actionable improvement tip. "
            f"{'Reply in friendly Hinglish/Hindi.' if is_hindi else 'Reply in English.'} "
            f"Do not modify the score. Return JSON format with keys 'summary' and 'tip'."
        )
        
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENAI_API_KEY}"
            },
            data=json.dumps({
                "model": OPENAI_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "response_format": {"type": "json_object"}
            }).encode("utf-8")
        )
        
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode("utf-8"))
            parsed = json.loads(result["choices"][0]["message"]["content"])
            return {
                "mode": "openai",
                "badge": "OpenAI AI Mode",
                "summary": parsed.get("summary", ""),
                "improvement_tip": parsed.get("tip", "")
            }
    except Exception as e:
        # Fallback cleanly on error
        return {
            "mode": "demo",
            "badge": "Offline Demo Mode (Fallback)",
            "summary": f"Your preparation for {role_title} stands at {readiness_score}%.",
            "improvement_tip": "Focus on the core milestones detailed in your custom roadmap."
        }
