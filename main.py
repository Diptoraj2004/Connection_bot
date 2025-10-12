# Patched: 2025-09-14 - production-ready entrypoint
"""
Entrypoint for the Crusade backend.
Provides console mode (interactive), Flask server launcher, and utility commands.
"""

import argparse
import os
import sys
from config import DEBUG
from web_adapter import run_app
from chatbot_flow import ChatSession
from iot_adapter import simulate_reading

def console_mode():
    print("Crusade console mode. Type 'exit' to quit.")
    sess = ChatSession(channel="console", user_id="console_user")
    out = sess.start_onboarding()
    print(out)
    while True:
        text = input("> ").strip()
        if text.lower() in ("exit", "quit"):
            print("Goodbye.")
            break
        # simple routing based on session state
        if sess.state == "ONBOARD":
            reply = sess.receive_onboard(text)
        elif sess.state == "MOOD_PROMPT":
            reply = sess.receive_mood(text)
        elif sess.state == "SCREENING_Q":
            reply = sess.receive_answer(text)
        elif sess.state == "APPOINTMENT_FLOW":
            reply = sess.handle_post_screening_choice(text)
        else:
            # fallback
            if "name" not in sess.persona:
                reply = sess.receive_onboard(text)
            elif "year" not in sess.persona:
                reply = sess.receive_year(text)
            else:
                reply = sess.receive_mood(text)
        print(reply)

def migrate_db():
    print("Running DB migration: (no-op in this reference implementation).")
    print("Apply SQL DDL in your Postgres / Supabase instance using the provided schema file.")

def export_ml(since: str = None):
    print(f"Exporting ML dataset to {os.getenv('ML_EXPORT_PATH', './ml_exports')}")
    # Implementation note: add production exporter (parquet/csv) that queries DB
    print("Export completed (placeholder).")

def run_workers():
    print("Starting background worker (placeholder). In production, run Celery/RQ/worker.")
    # Example: simulate periodic IoT spikes in background (not continuous here)
    for i in range(3):
        simulate_reading(user_id="console_user", metric_type="heart_rate")

def main():
    parser = argparse.ArgumentParser(description="Crusade backend runner")
    parser.add_argument("--console", action="store_true", help="Run console interactive mode")
    parser.add_argument("--flask", action="store_true", help="Run Flask web server")
    parser.add_argument("--migrate-db", action="store_true", help="Run DB migrations (placeholder)")
    parser.add_argument("--export-ml", action="store_true", help="Export ML dataset")
    parser.add_argument("--run-workers", action="store_true", help="Run background workers (placeholder)")
    args = parser.parse_args()

    if args.console:
        console_mode()
    elif args.migrate_db:
        migrate_db()
    elif args.export_ml:
        export_ml()
    elif args.run_workers:
        run_workers()
    elif args.flask:
        run_app()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
