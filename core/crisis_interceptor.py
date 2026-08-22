"""
core/crisis_interceptor.py — Deterministic Crisis Detection Layer.

This fires BEFORE the LLM. If triggered, it bypasses RAG entirely
and returns a hardcoded crisis response + logs to the Merkle Ledger.

Two-tier detection:
  1. Keyword match (immediate, zero-latency)
  2. ML severity escalation (from screening scores)
"""
from config import settings


CRISIS_RESPONSE = (
    "🚨 I want you to know that you matter deeply, and right now I need you to reach out "
    "to someone who can help immediately.\n\n"
    "📞 **Kiran Mental Health Helpline**: 1800-599-0019 (Free, 24/7, multilingual)\n"
    "📞 **AASRA**: 91-22-27546669 (24/7)\n"
    "📞 **Vandrevala Foundation**: 1860-2662-345 (24/7)\n"
    "📞 **iCall (TISS)**: 9152987821 (Mon–Sat, 8am–10pm)\n\n"
    "You are not alone. A trained counselor is available right now. "
    "Please call or WhatsApp one of these numbers — they are confidential and free.\n\n"
    "Where are you right now? Are you somewhere safe? 🙏"
)


def check_crisis_keywords(text: str) -> dict:
    """
    Scan text for crisis keywords.
    Returns: {"is_crisis": bool, "matched": list[str], "response": str|None}
    """
    text_lower = text.lower()
    matched = [kw for kw in settings.crisis_keywords if kw in text_lower]

    if matched:
        return {
            "is_crisis": True,
            "matched_keywords": matched,
            "response": CRISIS_RESPONSE,
            "trigger": "keyword",
        }

    return {"is_crisis": False, "matched_keywords": [], "response": None, "trigger": None}


def check_screening_escalation(test_name: str, score: int, severity: str) -> dict:
    """
    Check if a completed screening score warrants crisis escalation.
    Used after scoring any questionnaire.
    """
    thresh = settings.escalation_thresholds.get(test_name.lower(), {})
    escalate = False

    severe_thresh = thresh.get("severe", thresh.get("refer", 999))
    if score >= severe_thresh:
        escalate = True

    return {
        "escalate": escalate,
        "test_name": test_name,
        "score": score,
        "severity": severity,
        "trigger": "screening_score" if escalate else None,
    }


def log_crisis_event(user_id: str, trigger: str, details: dict):
    """Log a crisis event to the Merkle Ledger."""
    try:
        from core.merkle_ledger import log_event
        log_event(
            user_id=user_id,
            event_type=f"CRISIS_{trigger.upper()}",
            metadata=details,
            notify_counselor=True,
        )
    except Exception as e:
        print(f"[CRISIS] Ledger log failed: {e}")


def get_emergency_contacts_text() -> str:
    """Return formatted emergency contact list."""
    lines = []
    for key, contact in settings.emergency_contacts.items():
        lines.append(f"• {contact['name']}: {contact['number']} ({contact['hours']})")
    return "\n".join(lines)
