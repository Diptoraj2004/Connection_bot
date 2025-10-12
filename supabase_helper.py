# Patched: 2025-09-14 - production
"""
Supabase / Postgres helper abstraction.
Provides a consistent API for logging responses, scores, alerts, IoT readings, and ML export.
This module is written to work with either a Supabase HTTP client or a direct Postgres connection.
Replace the simple DB layer with your preferred client for production (supabase-py, asyncpg, SQLAlchemy).
"""

import os
import json
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, List

from config import DATABASE_URL, SUPABASE_KEY, LOCAL_SAVE_PATH

# Minimal safe local fallback file for queueing writes when DB is unavailable.
LOCAL_FALLBACK = os.getenv("LOCAL_SAVE_PATH", LOCAL_SAVE_PATH)

def _utcnow_iso():
    return datetime.utcnow().isoformat()

# Simple local persistence helpers (used as fallback)
def _append_local(record_type: str, payload: Dict[str, Any]):
    """Append a JSON record to local fallback file for debugging / retry."""
    entry = {"type": record_type, "ts": _utcnow_iso(), "payload": payload}
    p = LOCAL_FALLBACK
    try:
        if not os.path.exists(p):
            with open(p, "w", encoding="utf-8") as fh:
                json.dump([entry], fh, ensure_ascii=False, indent=2)
            return
        with open(p, "r+", encoding="utf-8") as fh:
            try:
                data = json.load(fh)
            except Exception:
                data = []
            data.append(entry)
            fh.seek(0)
            json.dump(data, fh, ensure_ascii=False, indent=2)
    except Exception:
        # best-effort ignore
        traceback.print_exc()

# NOTE: Replace the implementations below with calls to your DB client (Supabase, psycopg2, SQLAlchemy)
# For this deliverable, functions write to local fallback and return dicts that mimic DB responses.

def log_response(user_id: Optional[str], session_id: Optional[str], channel: str,
                 test_name: str, question_id: str, question_text: str,
                 answer_text: str, numeric_value: Optional[int],
                 modality: str = "text", locale: str = "en", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Record a single question/answer in responses (ML-ready).
    """
    record = {
        "session_id": session_id,
        "user_id": user_id,
        "channel": channel,
        "test_name": test_name,
        "question_id": question_id,
        "question_text": question_text,
        "answer_text": answer_text,
        "numeric_value": numeric_value,
        "modality": modality,
        "response_locale": locale,
        "metadata": metadata or {},
        "created_at": _utcnow_iso()
    }
    # In production: insert into DB. Here: append to local fallback for reliability.
    _append_local("response", record)
    return {"status": "ok", "record": record}

def insert_iot_reading(user_id: Optional[str], metric_type: str, value: float,
                       ts: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Insert IoT reading. Should match iot_adapter interface.
    """
    rec = {
        "user_id": user_id,
        "metric_type": metric_type,
        "value": value,
        "unit": metadata.get("unit") if metadata else None,
        "ts": ts or _utcnow_iso(),
        "source": metadata.get("source") if metadata else None,
        "metadata": metadata or {}
    }
    _append_local("iot_reading", rec)
    return {"status": "ok", "record": rec}

def create_alert(user_id: Optional[str], session_id: Optional[str], test_name: str,
                 score: int, level: str = "warning", details: Optional[Dict[str, Any]] = None,
                 notify_methods: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Create an alert / escalation record and return it. Also schedules notifications via worker.
    notify_methods example: ['email','whatsapp','sms','emergency_contact']
    """
    alert = {
        "user_id": user_id,
        "session_id": session_id,
        "test_name": test_name,
        "score": score,
        "level": level,
        "notify_methods": notify_methods or [],
        "notify_log": [],
        "visible_to_counsellor": True,
        "visible_to_institute": True,
        "resolved": False,
        "created_at": _utcnow_iso()
    }
    _append_local("alert", alert)
    # In production: trigger background notification worker here
    return {"status": "ok", "alert": alert}

def upsert_progress(user_id: str, progress: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update or insert a user's progress/streak record.
    progress: {"last_mood_date": "YYYY-MM-DD", "streak": int, "total_entries": int, "trend": {...}}
    """
    payload = {"user_id": user_id, "progress": progress, "updated_at": _utcnow_iso()}
    _append_local("progress", payload)
    return {"status": "ok", "payload": payload}

def get_user_scores(user_id: str, since: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Return a list of score records for ML or counselor. Here we read local fallback and filter.
    """
    try:
        if not os.path.exists(LOCAL_FALLBACK):
            return []
        with open(LOCAL_FALLBACK, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        scores = [e["payload"] for e in data if e["type"] == "score"]
        return [s for s in scores if s.get("user_id") == user_id]
    except Exception:
        return []

def bulk_insert_responses_for_ml(batch: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Bulk insert responses (for ML export or backfill). For now append each record to local fallback.
    """
    for rec in batch:
        _append_local("response", rec)
    return {"status": "ok", "inserted": len(batch)}

# Lightweight helper to record an aggregated score (not shown to student)
def record_score(user_id: Optional[str], session_id: Optional[str], test_name: str, raw_score: int, interpreted: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    score = {
        "user_id": user_id,
        "session_id": session_id,
        "test_name": test_name,
        "raw_score": raw_score,
        "interpreted": interpreted,
        "details": details or {},
        "created_at": _utcnow_iso()
    }
    _append_local("score", score)
    return {"status": "ok", "score": score}

# Basic connectivity check
def health_check() -> Dict[str, Any]:
    # In production: check DB/supabase status; here we return accessible
    return {"status": "ok", "backend": "local-fallback"}
