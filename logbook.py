# logbook.py
import sys
import speech_recognition as sr
from supabase_helper import get_sb_client
from config import USER_ID

from datetime import datetime, timezone


def get_voice_input() -> str:
    """Listens for voice input from the microphone and converts it to text."""
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("\n🗣️ Speak your logbook entry now...")
            r.adjust_for_ambient_noise(source)
            audio = r.listen(source, phrase_time_limit=30)

        print("⏳ Recognizing speech...")
        text = r.recognize_google(audio)  # Google Web Speech API
        return text

    except sr.UnknownValueError:
        print("❌ Could not understand audio.")
        return ""
    except sr.RequestError as e:
        print(f"❌ Speech recognition service error: {e}")
        return ""
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        return ""


def save_logbook_entry(sb, user_id, entry_text, share_with_counselor=False):
    """
    Saves a logbook entry to Supabase (table: logbook).
    Falls back to printing if Supabase is unavailable.
    """
    row = {
        "user_id": user_id,
        "entry": entry_text,
        "share_with_counselor": share_with_counselor,
        "ts": datetime.now(timezone.utc).isoformat()
    }
    try:
        if sb:
            sb.table("logbook").insert(row).execute()
            print("✅ Logbook entry saved to Supabase.")
        else:
            print("⚠️ No Supabase client, skipping DB insert.")
    except Exception as e:
        print(f"⚠️ Failed to save logbook entry: {e}")


def ask_logbook_entry(sb, user_id):
    """
    Prompts the user to write a logbook entry and asks for sharing preference.
    """
    print("\n📓 Logbook Entry")
    print("---------------------------")
    print("1. Type it out")
    print("2. Speak it (Voice-to-Text)")

    choice = input("Select an option (1/2): ").strip()

    log_entry = ""
    if choice == "2":
        log_entry = get_voice_input()
    else:
        print("\n✍️ Write your logbook entry for today:")
        log_entry = input("→ ").strip()

    if not log_entry:
        print("❌ Logbook entry cannot be empty. Skipping.")
        return

    print("\nDo you want to share this entry with a counsellor? (yes/no)")
    share_counselor = input("→ ").strip().lower()
    share_status = share_counselor == "yes"

    save_logbook_entry(sb, user_id, log_entry, share_with_counselor=share_status)


def main():
    """Main function to run the logbook script standalone."""
    sb = get_sb_client()
    print("Welcome to the Logbook feature!")
    ask_logbook_entry(sb, USER_ID)


if __name__ == "__main__":
    main()