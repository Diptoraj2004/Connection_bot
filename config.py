"""
config.py — SentinelMind v5 Production Configuration.

APP_MODE controls ALL behaviour:
  1 = TESTING   — Free tiers, JSON DB, Twilio sandbox, English RAG, simulated IoT
  2 = BUSINESS  — Free tiers still, but noise-robust IoT, multilingual RAG,
                  real Supabase, real Twilio, Redis cache, motion filtering,
                  longitudinal baselines, consent management

Change mode by setting APP_MODE=1 or APP_MODE=2 in your .env file.
Both modes use exclusively free-tier services.
"""
import os
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):

    # ── MODE ──────────────────────────────────────────────────────────────────
    app_mode: int = Field(default=1, env="APP_MODE")

    @property
    def is_testing(self) -> bool:
        return self.app_mode != 2

    @property
    def is_business(self) -> bool:
        return self.app_mode == 2

    # ── API KEYS ──────────────────────────────────────────────────────────────
    groq_api_key: str       = Field(default="", env="GROQ_API_KEY")
    ngrok_auth_token: str   = Field(default="", env="NGROK_AUTH_TOKEN")
    secret_key: str         = Field(default="sentinelmind-dev-secret", env="SECRET_KEY")

    # ── TWILIO / WHATSAPP ─────────────────────────────────────────────────────
    twilio_account_sid: str   = Field(default="", env="TWILIO_ACCOUNT_SID")
    twilio_auth_token: str    = Field(default="", env="TWILIO_AUTH_TOKEN")
    twilio_whatsapp_from: str = Field(default="whatsapp:+14155238886", env="TWILIO_WHATSAPP_FROM")
    enable_whatsapp: bool     = Field(default=False, env="ENABLE_WHATSAPP")

    # ── DATABASE ──────────────────────────────────────────────────────────────
    supabase_url: str  = Field(default="", env="SUPABASE_URL")
    supabase_key: str  = Field(default="", env="SUPABASE_KEY")
    local_db_path: str = "sentinel_db.json"

    @property
    def use_supabase(self) -> bool:
        return self.is_business and bool(self.supabase_url) and bool(self.supabase_key)

    # ── REDIS (Mode 2 only — Upstash free: 10K req/day) ──────────────────────
    redis_url: str = Field(default="", env="REDIS_URL")

    @property
    def use_redis(self) -> bool:
        return self.is_business and bool(self.redis_url)

    # ── WEARABLE OAUTH (Mode 2 only) ──────────────────────────────────────────
    fitbit_client_id: str     = Field(default="", env="FITBIT_CLIENT_ID")
    fitbit_client_secret: str = Field(default="", env="FITBIT_CLIENT_SECRET")
    google_fit_client_id: str = Field(default="", env="GOOGLE_FIT_CLIENT_ID")
    google_fit_secret: str    = Field(default="", env="GOOGLE_FIT_CLIENT_SECRET")
    app_base_url: str         = Field(default="http://localhost:8000", env="APP_BASE_URL")

    # ── LLM / RAG ─────────────────────────────────────────────────────────────
    groq_model: str                   = "llama-3.1-8b-instant"
    embedding_model: str              = "all-MiniLM-L6-v2"
    multilingual_embedding_model: str = "sentence-transformers/LaBSE"
    llm_max_tokens: int               = 200
    llm_temperature: float            = 0.1
    rag_top_k: int                    = 3

    @property
    def active_embedding_model(self) -> str:
        return self.multilingual_embedding_model if self.is_business else self.embedding_model

    # ── WHISPER ───────────────────────────────────────────────────────────────
    whisper_model: str   = Field(default="base", env="WHISPER_MODEL")
    enable_whisper: bool = Field(default=True,   env="ENABLE_WHISPER")

    # ── IOT THRESHOLDS ────────────────────────────────────────────────────────
    iot_heart_rate_high: int   = 130
    iot_heart_rate_low: int    = 45
    iot_spo2_low: float        = 94.0
    iot_sleep_low_hours: float = 5.0
    iot_gsr_high: float        = 4.0
    # Mode 2: noise filtering
    iot_rolling_window: int    = 5    # readings required before alert
    iot_motion_threshold: float= 2.0  # g-force above which HR reading is discarded

    # ── BASELINE ──────────────────────────────────────────────────────────────
    baseline_days: int              = 7
    baseline_std_threshold: float   = 1.5  # deviations from personal mean

    # ── SESSION ───────────────────────────────────────────────────────────────
    session_ttl_minutes: int     = 120
    followup_reminder_hours: int = Field(default=48, env="FOLLOWUP_REMINDER_HOURS")
    inactivity_alert_days: int   = Field(default=5,  env="INACTIVITY_ALERT_DAYS")
    enable_parent_share: bool    = Field(default=False, env="ENABLE_PARENT_SHARE")

    # ── LANGUAGES ─────────────────────────────────────────────────────────────
    @property
    def active_languages(self) -> list:
        if self.is_business:
            return ["en", "hi", "ta", "te", "bn", "kn", "mr", "gu"]
        return ["en"]

    # ── CONSENT FEATURES ──────────────────────────────────────────────────────
    consent_required_features: list = [
        "camera_analysis", "voice_prosody", "iot_monitoring",
        "typing_patterns", "usage_patterns", "parent_share",
    ]

    # ── CRISIS ────────────────────────────────────────────────────────────────
    crisis_keywords: list = [
        "suicide", "suicidal", "kill myself", "end my life", "want to die",
        "harm myself", "self harm", "self-harm", "cut myself",
        "no reason to live", "better off dead", "can't go on",
    ]
    emergency_contacts: dict = {
        "kiran":       {"name": "Kiran Mental Health Helpline", "number": "1800-599-0019",  "hours": "24/7"},
        "aasra":       {"name": "AASRA",                        "number": "91-22-27546669", "hours": "24/7"},
        "vandrevala":  {"name": "Vandrevala Foundation",        "number": "1860-2662-345",  "hours": "24/7"},
        "icall":       {"name": "iCall (TISS)",                 "number": "9152987821",     "hours": "Mon-Sat 8am-10pm"},
        "antiragging": {"name": "UGC Anti-Ragging Helpline",   "number": "1800-180-5522",  "hours": "24/7"},
    }

    # ── ESCALATION TIMEOUTS ───────────────────────────────────────────────────
    escalation_timeouts: dict = {
        "L1_WATCH": None, "L2_ALERT": 60, "L3_URGENT": 30, "L4_CRITICAL": 15
    }

    # ── GAMIFICATION ──────────────────────────────────────────────────────────
    points_per_mood_log: int         = 10
    points_per_screening: int        = 25
    points_per_logbook: int          = 15
    points_per_session_complete: int = 30
    points_per_study_session: int    = 20
    points_per_sleep_log: int        = 15
    points_per_peer_help: int        = 20

    # ── ACADEMIC RISK WINDOWS ─────────────────────────────────────────────────
    academic_risk_windows: list = [
        {"name": "Mid-semester exams",  "start": "03-01", "end": "03-20"},
        {"name": "End-semester exams",  "start": "05-01", "end": "05-31"},
        {"name": "Results window",      "start": "06-01", "end": "06-15"},
        {"name": "Admission stress",    "start": "07-01", "end": "07-31"},
        {"name": "End-semester exams",  "start": "11-01", "end": "11-30"},
        {"name": "Year-end results",    "start": "12-15", "end": "01-10"},
        {"name": "JEE/NEET pressure",   "start": "01-15", "end": "04-30"},
        {"name": "Placement season",    "start": "09-01", "end": "11-30"},
    ]

    # ── SCREENING THRESHOLDS ──────────────────────────────────────────────────
    escalation_thresholds: dict = {
        "phq-9":  {"moderate": 10, "severe": 15},
        "gad-7":  {"moderate": 10, "severe": 15},
        "ghq-12": {"moderate": 4,  "severe": 8},
        "k-10":   {"moderate": 20, "severe": 30},
        "aq10":   {"refer": 6},
        "asrs":   {"refer": 4},
        "sleep":  {"poor": 5},
    }

    ngo_price_tiers: dict = {
        "free":       {"max_inr": 0,    "label": "Free"},
        "subsidised": {"max_inr": 200,  "label": "Up to ₹200/session"},
        "low_cost":   {"max_inr": 500,  "label": "Up to ₹500/session"},
        "moderate":   {"max_inr": 1500, "label": "Up to ₹1500/session"},
    }

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

if settings.groq_api_key:
    os.environ["GROQ_API_KEY"] = settings.groq_api_key

_label = "🧪 TESTING (Mode 1)" if settings.is_testing else "🏢 BUSINESS (Mode 2)"
print(f"[CONFIG] SentinelMind v5 — {_label}")
