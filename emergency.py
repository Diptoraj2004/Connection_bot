import sys
from supabase_helper import get_sb_client
from config import USER_ID

# storing this info in Supabase DB or a separate config.
EMERGENCY_CONTACT = {
    "name": "Jane Doe",
    "phone": "+15551234567",
    "email": "jane.doe@example.com"
}

def check_for_emergency(text: str) -> bool:
    """
    Checks if the user's input indicates a severe symptom or emergency.
    This can be expanded with more sophisticated NLP techniques.
    """
    # List of keywords that may indicate an emergency.
    # This list should be comprehensive and carefully curated.
    emergency_keywords = [
        "suicidal", "hurting myself", "end it all", "self-harm", 
        "can't go on", "hopeless", "overdose", "emergency", "crisis",
        "serious symptoms", "severely depressed"
    ]
    # Check for keywords in the user's text, case-insensitively.
    if any(keyword in text.lower() for keyword in emergency_keywords):
        return True
    return False

def trigger_emergency_escalation(user_id: str, message: str):
    """
    Triggers an emergency alert. In a real-world app, this would send an SMS, email, or webhook.
    For this project, we'll print a clear, actionable message to the console.
    """
    print("\n\n🚨 🚨 🚨 EMERGENCY ALERT 🚨 🚨 🚨")
    print("-----------------------------------")
    print("Detected a high-risk situation. Notifying emergency contacts.")
    print(f"User ID: {user_id}")
    print(f"Message: '{message}'")
    print("-----------------------------------")
    print(f"Contact Name: {EMERGENCY_CONTACT['name']}")
    print(f"Phone: {EMERGENCY_CONTACT['phone']}")
    print(f"Email: {EMERGENCY_CONTACT['email']}")
    print("-----------------------------------")
    print("Please follow your established protocol for this type of event.")
    print("🚨 🚨 🚨 ALERT COMPLETE 🚨 🚨 🚨")

def main():
    """
    Main function to run the emergency script as a standalone test.
    """
    test_phrases = [
        "I'm feeling really happy today.",
        "I am feeling very sad and alone, I might be hurting myself.",
        "Everything is fine, thanks for asking.",
        "I just feel like I can't go on anymore."
    ]

    for phrase in test_phrases:
        print(f"\nTesting phrase: '{phrase}'")
        if check_for_emergency(phrase):
            trigger_emergency_escalation(USER_ID, phrase)
        else:
            print("No emergency keywords detected.")

if __name__ == "__main__":
    main()
