import sys
from supabase_helper import get_sb_client, upsert_response
from config import USER_ID

def ask_logbook_entry(sb, user_id):
    """
    Prompts the user to write a logbook entry and asks for sharing preference.
    """
    print("\n Write your logbook entry for today:")
    log_entry = input("→ ").strip()
    if not log_entry:
        print("Logbook entry cannot be empty. Skipping.")
        return

    # Store the logbook entry
    upsert_response(sb, user_id, "logbook_entry", "Logbook Entry", log_entry)

    print("\nDo you want to share this entry with a counsellor? (yes/no)")
    share_counsellor = input("→ ").strip().lower()

    # Store the sharing preference
    share_status = "Yes" if share_counsellor == "yes" else "No"
    upsert_response(sb, user_id, "share_counsellor", "Share with Counsellor", share_status)

    print("\nLogbook entry saved.")

def main():
    """
    Main function to run the logbook script.
    """
    sb = get_sb_client()
    print("Welcome to the Logbook feature!")
    ask_logbook_entry(sb, USER_ID)

if __name__ == "__main__":
    main()