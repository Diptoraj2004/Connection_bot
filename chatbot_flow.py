# chatbot_flow.py
import os, random
from datetime import datetime
from config import (
    USE_WATSON, LLM_PROVIDER, LLM_MODEL,
    MOOD_OPTIONS, MUSIC_SUGGESTIONS, ESCALATION_THRESHOLD
)
from data_loader import load_all_datasets
from supabase_helper import get_sb_client, upsert_response, set_progress, get_progress
from progress_store import (
    record_mood, record_sleep, get_current_streak, record_escalation, load_user_state, save_user_state
)
from iot_adapter import collect_iot_metrics

#logbook import
from logbook import ask_logbook_entry

#emergency contact import
from emergency import check_for_emergency, trigger_emergency_escalation

# Optional imports
try:
    from watson_helper import watson_available
except ImportError:
    watson_available = lambda: False

try:
    from groq import Groq
except ImportError:
    Groq = None


# ---------------------------
# LLM Helper
# ---------------------------
def llm_generate(prompt: str) -> str:
    """Generate a reply using configured LLM provider."""
    if LLM_PROVIDER == "groq" and Groq:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )
        return resp.choices[0].message["content"]
    return "⚠️ LLM provider not configured properly."


# ---------------------------
# Role Handling
# ---------------------------
def ask_user_role():
    """Ask or load role from state (student, counselor, institution)."""
    state = load_user_state()
    role = state.get("role")
    if role:
        return role

    print("\nWho are you?")
    print("1. Student / Patient")
    print("2. Counselor / Doctor")
    print("3. Institution")
    print("4. First-time User")
    choice = input("Select option: ").strip()
    role_map = {"1":"student","2":"counselor","3":"institution","4":"first_time"}
    role = role_map.get(choice, "student")

    state["role"] = role
    save_user_state(state)
    return role


# ---------------------------
# Mood + Sleep + Escalation
# ---------------------------
def ask_mood_sleep(sb, user_id):
    """Ask mood and sleep, log them, and check escalation logic."""
    print("\n--- Daily Check-in ---")
    for i, mood in enumerate(MOOD_OPTIONS):
        print(f"{i+1}. {mood}")
    choice = input("Mood today: ").strip()
    mood = MOOD_OPTIONS[int(choice)-1] if choice.isdigit() and 1 <= int(choice) <= len(MOOD_OPTIONS) else "Unknown"

    record_mood(mood)
    upsert_response(sb, user_id, "mood", "Daily Mood", mood)

    hours = input("Hours of sleep last night: ").strip()
    try: hours = int(hours)
    except: hours = 0
    record_sleep(hours)
    upsert_response(sb, user_id, "sleep", "Sleep Hours", str(hours))

    if mood.lower() in ["sad","anxious","angry"] or hours < 4:
        record_escalation("Low mood or poor sleep")
        print("⚠️ Escalation flagged.")

    streak = get_current_streak()
    print(f"🔥 Streak: {streak} days")


# ---------------------------
# Screening Flow
# ---------------------------
def run_screening_console():
    """Main chatbot flow (console-based)."""
    sb = None
    try: sb = get_sb_client()
    except: print("⚠️ Supabase unavailable, using local fallback.")

    user_id = "fixed_user"
    role = ask_user_role()

    if role == "student":
        datasets = load_all_datasets()
        if not datasets:
            print("❌ No datasets found.")
            return
        dataset_name = list(datasets.keys())[0]
        questions = datasets[dataset_name]

        progress = get_progress(sb, user_id)
        batch = questions[(progress-1)*10 : progress*10]

        ask_mood_sleep(sb, user_id)
        
        ask_logbook_entry(sb, user_id)

        iot_data = collect_iot_metrics()
        print("\n📊 IoT Metrics:", iot_data)

        print("\n--- Screening ---")
        for q in batch:
            print(q["text"])
            if q["options"]: print("Options:", ", ".join(q["options"]))
            ans = input("Answer: ").strip()
            upsert_response(sb, user_id, q["id"], q["text"], ans)

        set_progress(sb, user_id, progress+1)
        print(f"\n🎵 Music suggestion: {random.choice(MUSIC_SUGGESTIONS)}")
        
        user_msg = input("\n💬 Say something to AI: ").strip()
        
        # Emergency check is placed for students
        if check_for_emergency(user_msg):
            trigger_emergency_escalation(USER_ID, user_msg)
        else:
            if user_msg:
                reply = llm_generate(user_msg)
                print("AI:", reply)


    elif role == "counselor":
        print("\n📌 Counselor Dashboard (placeholder)")
        print(" - View escalation logs (to be implemented).")

    elif role == "institution":
        print("\n🏢 Institution Dashboard (placeholder)")
        print(" - Aggregate analytics of all users (to be implemented).")

    elif role == "first_time":
        print("\n👋 Welcome! Let’s set up your account.")
        print("Tell us if you’re a student, counselor, or institution (restart will save this).")

    print("\n✅ Session complete.")
