# SentinelMind Backend — Complete Reference

## Project Structure
```
sentinelmind/
├── main.py                  # FastAPI app entrypoint + CORS + router mounting
├── config.py                # All env vars, thresholds, constants
├── requirements.txt         # All pip dependencies
├── colab_runner.py          # One-cell Colab launcher (ngrok + uvicorn)
│
├── api/                     # Route handlers (thin controllers)
│   ├── chat.py              # /api/chat — core conversation gateway
│   ├── screening.py         # /api/screening — questionnaire CRUD
│   ├── iot.py               # /api/iot — wearable telemetry ingestion
│   ├── progress.py          # /api/progress — mood/streak/gamification
│   ├── logbook.py           # /api/logbook — encrypted private journal
│   ├── resources.py         # /api/resources — media hub + music AI
│   ├── booking.py           # /api/booking — counselor slot booking
│   └── admin.py             # /api/admin — anonymous trend dashboard
│
├── core/                    # Domain logic (business rules)
│   ├── session_manager.py   # In-memory session registry + cleanup
│   ├── chat_session.py      # Finite-state conversation machine
│   ├── crisis_interceptor.py# Keyword + NLP crisis detection
│   ├── pii_scrubber.py      # Microsoft Presidio wrapper
│   ├── merkle_ledger.py     # Immutable SHA-256 audit chain
│   └── scoring.py           # PHQ-9/GAD-7/AQ10/ASRS/GHQ-12 scoring + severity
│
├── services/                # External integrations
│   ├── rag_engine.py        # LangChain + FAISS + Groq (LLaMA 3)
│   ├── music_ai.py          # Mood → music recommendation engine
│   ├── iot_adapter.py       # IoT telemetry + threshold processing
│   ├── notification.py      # Webhook dispatcher (counselor/parent alerts)
│   └── ngo_directory.py     # NGO/counselor matchmaking
│
└── data/                    # Data layer (mock Supabase + questionnaires)
    ├── db.py                 # JSON-backed mock DB (drop-in Supabase later)
    ├── questionnaires.py     # Full PHQ-9/GAD-7/GHQ-12/AQ10/ASRS/K-10/Sleep
    └── progress_store.py     # Gamification + streak engine
```

## Quick Start (Google Colab)

1. Upload the entire `sentinelmind/` folder to your Colab runtime
2. Run `colab_runner.py` — it installs deps, sets keys, and starts ngrok
3. Point your frontend at the printed public URL

## Environment Variables
```
GROQ_API_KEY=gsk_...
NGROK_AUTH_TOKEN=...
SECRET_KEY=your-jwt-secret       # for future JWT auth
SUPABASE_URL=                    # optional, falls back to local JSON
SUPABASE_KEY=                    # optional
```

## API Endpoints Summary

| Method | Path | Purpose |
|--------|------|---------|
| POST | /api/chat | Main conversation (stateful) |
| POST | /api/screening/start | Begin a questionnaire |
| POST | /api/screening/answer | Submit an answer |
| GET  | /api/screening/result/{user_id} | Get scored result |
| POST | /api/iot/reading | Ingest wearable data |
| GET  | /api/progress/{user_id} | Mood/streak/badges |
| POST | /api/progress/mood | Log a mood entry |
| POST | /api/logbook/entry | Create encrypted logbook entry |
| GET  | /api/logbook/{user_id} | Retrieve logbook (consent-gated) |
| GET  | /api/resources | Get media by mood type |
| GET  | /api/resources/music | AI music suggestion |
| POST | /api/booking/slot | Book counselor session |
| GET  | /api/booking/slots | List available slots |
| GET  | /api/admin/trends | Anonymous aggregate trends |
| GET  | /api/admin/alerts | Recent escalation events |
| GET  | /health | Health check |
