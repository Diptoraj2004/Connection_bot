# logbook.py
"""
Logbook helper: text entry (and optional speech input if speech_recognition installed).
"""

from supabase_helper import add_logbook_entry
from config import USE_SPEECH

def get_voice_input():
    try:
        import speech_recognition as sr
    except Exception:
        print("Speech recognition not available. Please type your entry.")
        return ""
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("🗣️ Speak now (max 30s)...")
            r.adjust_for_ambient_noise(source, duration=0.8)
            audio = r.listen(source, phrase_time_limit=30)
        txt = r.recognize_google(audio)
        return txt
    except Exception as e:
        print("Voice input failed:", e)
        return ""

def ask_logbook_entry(sb, user_id):
    print("\nWould you like to add a logbook entry? (y/n)")
    c = input("→ ").strip().lower()
    if c not in ("y", "yes"):
        return
    if USE_SPEECH:
        txt = get_voice_input()
        if not txt:
            txt = input("Type your entry: ").strip()
    else:
        txt = input("Write your logbook entry: ").strip()
    if not txt:
        print("No entry recorded.")
        return
    share = input("Share with counsellor? (yes/no) ").strip().lower() in ("y", "yes")
    add_logbook_entry(user_id, txt, share_with_counselor=share)
    print("✅ Logbook saved.")
