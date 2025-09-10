"""
main.py
Entry point with unified login and role-based routing.
"""

from config import USER_ID
from chatbot_flow import run_screening_console
import iot_adapter

# TODO: hook to supabase for real user auth
USERS = {
    "student": {"password": "123", "role": "student"},
    "parent": {"password": "123", "role": "parent"},
    "counselor": {"password": "123", "role": "counselor"},
    "institution": {"password": "123", "role": "institution"},
}

def login():
    print("🔐 Login required")
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    user = USERS.get(username)
    if not user or user["password"] != password:
        print("❌ Invalid credentials")
        return None
    return {"id": username, "role": user["role"]}

def route_user(user):
    role = user["role"]
    uid = user["id"]

    if role == "student":
        print("\n🎓 Welcome Student")
        run_screening_console(uid)
        print("\n📊 IoT snapshot:", iot_adapter.collect_all_metrics(uid))

    elif role == "parent":
        print("\n👨‍👩‍👦 Welcome Parent")
        print("📖 You can view your child's logs and summaries (logbook integration pending).")

    elif role == "counselor":
        print("\n🧑‍⚕️ Welcome Counselor")
        print("📋 Dashboard: list of assigned students & flagged cases (integration pending).")

    elif role == "institution":
        print("\n🏫 Welcome Institution Admin")
        print("📊 Dashboard: overview of counselors, flagged students, and risk trends.")

    else:
        print("❌ Unknown role.")

if __name__ == "__main__":
    user = login()
    if user:
        route_user(user)
