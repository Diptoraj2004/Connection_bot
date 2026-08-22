"""
main.py — SentinelMind FastAPI Application v3.0
Complete entry point with all routers mounted.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "="*60)
    print("  SentinelMind Backend v3.0 — Starting Up")
    print("="*60)
    try:
        from core.pii_scrubber import _init; _init()
    except Exception as e:
        print(f"[STARTUP] PII: {e}")
    try:
        from services.ml_triage import is_model_trained
        print(f"[STARTUP] ML model: {'✅ Ready' if is_model_trained() else '⚠️  Not trained → POST /api/ml/train'}")
    except Exception as e:
        print(f"[STARTUP] ML: {e}")
    try:
        from core.merkle_ledger import verify_ledger_integrity
        r = verify_ledger_integrity()
        print(f"[STARTUP] Merkle Ledger: {'✅' if r['valid'] else '❌'} ({r['entries']} entries)")
    except Exception as e:
        print(f"[STARTUP] Ledger: {e}")
    try:
        from services.voice_service import is_whisper_available
        print(f"[STARTUP] Whisper: {'✅ Ready' if is_whisper_available() else '⚠️  Not installed → pip install openai-whisper'}")
    except Exception as e:
        print(f"[STARTUP] Whisper: {e}")
    try:
        from services.reminder_engine import get_current_risk_window
        window = get_current_risk_window()
        if window:
            print(f"[STARTUP] ⚠️  Academic risk window active: {window['window_name']}")
    except Exception as e:
        print(f"[STARTUP] Risk window: {e}")
    print("="*60 + "\n")
    # Start background session cleanup to prevent unbounded memory growth
    try:
        from core.session_manager import start_cleanup_thread
        start_cleanup_thread(interval_minutes=30)
    except Exception as e:
        print(f"[STARTUP] Cleanup thread: {e}")
    yield
    print("\n[SHUTDOWN] SentinelMind shutting down.")


app = FastAPI(
    title="SentinelMind — Digital Mental Health API v3.0",
    description=(
        "Privacy-first, RAG-powered mental health backend for Indian college campuses. "
        "AI chatbot | PHQ-9/GAD-7/GHQ-12/AQ-10/ASRS/K-10/Sleep screening | "
        "IoT telemetry | Merkle crisis ledger | Escalation chain | "
        "WhatsApp integration | Voice-to-text logbook | "
        "NGO financial matching | Peer stories | Volunteer management | "
        "Counselor session notes | Bullying detection | Academic risk windows"
    ),
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Mount all routers ─────────────────────────────────────────────────────────
from api.routes import (
    chat_router, screening_router, iot_router,
    progress_router, logbook_router, resources_router,
    booking_router, admin_router, ml_router,
    escalation_router, ngo_router, volunteer_router,
    counselor_router, stories_router, voice_router,
    whatsapp_router, reminder_router, rating_router,
    passive_router,
    consent_router, engage_router, silent_router,
    wearable_router, baseline_router, jobs_router,
    phenotype_router, memory_router, zones_router, payment_router,
)

for router in [
    chat_router, screening_router, iot_router,
    progress_router, logbook_router, resources_router,
    booking_router, admin_router, ml_router,
    escalation_router, ngo_router, volunteer_router,
    counselor_router, stories_router, voice_router,
    whatsapp_router, reminder_router, rating_router,
    passive_router,
    consent_router, engage_router, silent_router,
    wearable_router, baseline_router, jobs_router,
    phenotype_router, memory_router, zones_router, payment_router,
]:
    app.include_router(router)


# ── Utility endpoints ─────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health():
    from core.session_manager import active_count
    from services.ml_triage import is_model_trained
    from services.voice_service import is_whisper_available
    from services.volunteer_manager import get_available_count
    from services.reminder_engine import get_current_risk_window
    return {
        "status":            "healthy",
        "version":           "3.0.0",
        "active_sessions":   active_count(),
        "ml_ready":          is_model_trained(),
        "whisper_ready":     is_whisper_available(),
        "volunteers_online": get_available_count(),
        "risk_window":       get_current_risk_window(),
    }

@app.get("/", tags=["System"])
async def root():
    return {"message": "SentinelMind API v3.0", "docs": "/docs", "health": "/health"}

# Legacy shims
@app.post("/analyze-text", include_in_schema=False)
@app.get("/analyze-text",  include_in_schema=False)
async def _legacy_analyze(): return {"status": "success", "use": "/api/chat"}

@app.get("/songs", include_in_schema=False)
async def _legacy_songs():
    from services.music_ai import get_resources_json
    return {"resource": get_resources_json("neutral")[0]}

@app.exception_handler(Exception)
async def _global_exc(request: Request, exc: Exception):
    print(f"[ERROR] {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal error"})
