# emergency.py
"""
Detects emergency keywords and formats an escalation message.
"""

EMERGENCY_CONTACT = {
    "name": "Campus Counselor",
    "phone": "+911234567890",
    "email": "counselor@example.edu"
}

EMERGENCY_KEYWORDS = [
    "suicide", "suicidal", "kill myself", "hurt myself", "end my life",
    "i will die", "can't go on", "overdose", "panic attack help", "i'm going to die"
]

def check_emergency(text: str):
    if not text:
        return None
    t = text.lower()
    for k in EMERGENCY_KEYWORDS:
        if k in t:
            # return a user-facing escalation message
            return (
                "🚨 I am concerned about your safety. "
                "I've flagged this message for urgent review and recommend contacting local emergency services now. "
                f"Emergency contact: {EMERGENCY_CONTACT['name']} ({EMERGENCY_CONTACT['phone']})."
            )
    return None

def trigger_emergency_escalation(user_id: str, text: str):
    # For demo: print to console and store in local progress via supabase_helper
    print("\n=== EMERGENCY ESCALATION ===")
    print("User:", user_id)
    print("Message:", text)
    print("Contact:", EMERGENCY_CONTACT)
    print("===========================")
    try:
        from supabase_helper import create_alert
        create_alert(user_id, level="high", reason="suicidal ideation", target="counselor", meta={"text": text})
    except Exception:
        pass
