# Patched: 2025-09-14 - production-ready
"""
Configuration and constants for Crusade Codex backend.
Reads values from environment variables.
"""

import os
from typing import Dict

# Basic env helpers
def _bool_env(key: str, default: bool) -> bool:
    val = os.getenv(key)
    if val is None:
        return default
    return val.lower() in ("1", "true", "yes", "y", "t")

def _int_env(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, default))
    except Exception:
        return default

# App behavior
DEBUG = _bool_env("DEBUG", False)
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
SECRET_KEY = os.getenv("FLASK_SECRET", "change-me-in-prod")

# Database / Supabase
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Local persistence fallback
LOCAL_SAVE_PATH = os.getenv("LOCAL_SAVE_PATH", "local_progress.json")
ML_EXPORT_PATH = os.getenv("ML_EXPORT_PATH", "./ml_exports")
ML_FEATURE_WINDOW_DAYS = _int_env("ML_FEATURE_WINDOW_DAYS", 30)

# OAuth / Auth
USE_GOOGLE_OAUTH = _bool_env("USE_GOOGLE_OAUTH", True)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_OAUTH_REDIRECT = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "/auth/google/callback")

# Twilio / Notifications
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")  # e.g. 'whatsapp:+1415xxxxxxx' or SMS number
TWILIO_SMS_FROM = os.getenv("TWILIO_SMS_FROM")
TWILIO_NOTIFY_ENABLED = _bool_env("TWILIO_NOTIFY_ENABLED", True)

# Email SMTP
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SMTP_FROM = os.getenv("SMTP_FROM", "Crusade <noreply@crusade.example>")

# LLM / NLP / translation
USE_LLM = _bool_env("USE_LLM", True)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# IoT toggles
USE_SIMULATION = _bool_env("USE_SIMULATION", True)
USE_GOOGLE_FIT = _bool_env("USE_GOOGLE_FIT", False)
USE_APPLE_HEALTH = _bool_env("USE_APPLE_HEALTH", False)
USE_FITBIT = _bool_env("USE_FITBIT", False)
USE_SAMSUNG_HEALTH = _bool_env("USE_SAMSUNG_HEALTH", False)

# Localization
SUPPORTED_LOCALES = os.getenv("SUPPORTED_LOCALES", "en,hi,bn,ks").split(",")
PRIORITY_LOCALES = ["hi", "bn", "ks"]

# Escalation thresholds (defaults; override via env if needed)
ESCALATION_THRESHOLDS: Dict[str, int] = {
    "PHQ-9": _int_env("PHQ9_THRESHOLD", 15),
    "GAD-7": _int_env("GAD7_THRESHOLD", 15),
    "GHQ-12": _int_env("GHQ12_THRESHOLD", 5),
    "SLEEP": _int_env("SLEEP_THRESHOLD", 4),
    # others may be added per-questionnaire
}

# Notification defaults and priority
ALERT_NOTIFY_PRIORITY = os.getenv("ALERT_NOTIFY_PRIORITY", "email,whatsapp,sms,emergency_contact").split(",")
ALERT_NOTIFY_DEFAULTS = ALERT_NOTIFY_PRIORITY

# Score visibility policy
# Students do not see raw numeric scores
SCORE_VISIBLE_TO_STUDENT = False
SCORE_VISIBLE_TO_COUNSELLOR = True
SCORE_VISIBLE_TO_INSTITUTE = True

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Misc
APP_NAME = "CrusadeCodex(Temporary)"
