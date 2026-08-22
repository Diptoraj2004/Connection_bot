"""
data/db.py — Mode-aware data layer.

Mode 1 (Testing):  Local JSON file — zero setup, works immediately in Colab.
Mode 2 (Business): Supabase (PostgreSQL free tier, 500MB, unlimited requests).
                   Falls back to JSON if Supabase credentials not set.

All public functions have the same signature in both modes.
Swap modes by changing APP_MODE in .env — no code changes needed.
"""
import json
import os
import uuid
from datetime import datetime
from typing import Any, Optional
from config import settings

_DB_PATH = settings.local_db_path
_supabase_client = None


# ── Supabase client (Mode 2) ──────────────────────────────────────────────────

def _get_supabase():
    global _supabase_client
    if _supabase_client:
        return _supabase_client
    if not settings.use_supabase:
        return None
    try:
        from supabase import create_client
        _supabase_client = create_client(settings.supabase_url, settings.supabase_key)
        return _supabase_client
    except Exception as e:
        print(f"[DB] Supabase init failed ({e}) — falling back to JSON")
        return None


# ── Redis cache (Mode 2 optional) ─────────────────────────────────────────────

def _get_redis():
    if not settings.use_redis:
        return None
    try:
        import redis
        return redis.from_url(settings.redis_url, decode_responses=True)
    except Exception:
        return None


# ── JSON fallback helpers ─────────────────────────────────────────────────────

def _jload() -> list:
    if not os.path.exists(_DB_PATH):
        return []
    try:
        with open(_DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _jsave(data: list) -> None:
    try:
        with open(_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"[DB] JSON write error: {e}")


# ── Core public API ───────────────────────────────────────────────────────────

def insert_record(record_type: str, payload: dict) -> dict:
    """Insert a record. Uses Supabase in Mode 2, JSON in Mode 1."""
    record = {
        "id":      str(uuid.uuid4()),
        "type":    record_type,
        "ts":      datetime.utcnow().isoformat(),
        "payload": payload,
    }
    sb = _get_supabase()
    if sb:
        try:
            sb.table("sentinel_records").insert({
                "id":          record["id"],
                "record_type": record_type,
                "ts":          record["ts"],
                "payload":     payload,
            }).execute()
            return record
        except Exception as e:
            print(f"[DB] Supabase insert failed ({e}) — falling back to JSON")
    # JSON fallback
    data = _jload()
    data.append(record)
    _jsave(data)
    return record


def query_records(record_type: str, filters: dict = None, limit: int = 500) -> list:
    """Query records by type + optional field filters."""
    sb = _get_supabase()
    if sb:
        try:
            q = sb.table("sentinel_records").select("*").eq("record_type", record_type)
            if filters:
                for k, v in filters.items():
                    q = q.eq(f"payload->{k}", v)
            result = q.limit(limit).execute()
            return [{**r["payload"], "_ts": r["ts"], "_id": r["id"]}
                    for r in result.data]
        except Exception as e:
            print(f"[DB] Supabase query failed ({e}) — falling back to JSON")
    # JSON fallback
    results = []
    for record in _jload():
        if record.get("type") != record_type:
            continue
        payload = record.get("payload", {})
        if filters and not all(payload.get(k) == v for k, v in filters.items()):
            continue
        results.append({**payload, "_ts": record["ts"], "_id": record["id"]})
    return results[-limit:]


def get_latest(record_type: str, filters: dict = None) -> Optional[dict]:
    results = query_records(record_type, filters)
    return results[-1] if results else None


# ── Domain-specific helpers ───────────────────────────────────────────────────

def save_chat_message(user_id: str, session_id: str, role: str,
                      content: str, metadata: dict = None) -> dict:
    return insert_record("chat_message", {
        "user_id": user_id, "session_id": session_id,
        "role": role, "content": content, "metadata": metadata or {},
    })


def get_chat_history(user_id: str, session_id: str = None, limit: int = 50) -> list:
    filters = {"user_id": user_id}
    if session_id:
        filters["session_id"] = session_id
    return query_records("chat_message", filters)[-limit:]


def save_screening_result(user_id: str, test_name: str, score: int,
                          severity: str, escalate: bool,
                          answers: list, interpretation: str) -> dict:
    return insert_record("screening_result", {
        "user_id": user_id, "test_name": test_name, "score": score,
        "severity": severity, "escalate": escalate,
        "answers": answers, "interpretation": interpretation,
    })


def get_screening_results(user_id: str) -> list:
    return query_records("screening_result", {"user_id": user_id})


def get_latest_screening(user_id: str, test_name: str = None) -> Optional[dict]:
    results = query_records("screening_result", {"user_id": user_id})
    if test_name:
        results = [r for r in results if r.get("test_name") == test_name]
    return results[-1] if results else None


def save_mood_log(user_id: str, mood_score: int, mood_label: str,
                  note: str = "", tags: list = None) -> dict:
    return insert_record("mood_log", {
        "user_id": user_id, "mood_score": mood_score,
        "mood_label": mood_label, "note": note, "tags": tags or [],
    })


def get_mood_logs(user_id: str, limit: int = 30) -> list:
    return query_records("mood_log", {"user_id": user_id})[-limit:]


def save_logbook_entry(user_id: str, content_encrypted: str,
                       consent_level: str, audio_transcript: str = "",
                       tags: list = None) -> dict:
    return insert_record("logbook_entry", {
        "user_id":           user_id,
        "content_encrypted": content_encrypted,
        "consent_level":     consent_level,
        "audio_transcript":  audio_transcript,
        "tags":              tags or [],
    })


def get_logbook_entries(user_id: str, requester_role: str = "student") -> list:
    all_entries = query_records("logbook_entry", {"user_id": user_id})
    if requester_role == "student":
        return all_entries
    elif requester_role == "counselor":
        return [e for e in all_entries
                if e.get("consent_level") in ("counselor_only", "partial_parent")]
    elif requester_role == "parent":
        return [e for e in all_entries if e.get("consent_level") == "partial_parent"]
    return []


def save_progress(user_id: str, progress: dict) -> dict:
    return insert_record("progress", {"user_id": user_id, "progress": progress})


def get_progress(user_id: str) -> Optional[dict]:
    result = get_latest("progress", {"user_id": user_id})
    return result.get("progress") if result else None


def save_iot_reading(user_id: str, metric_type: str, value: float,
                     ts: str, threshold_breached: bool = False,
                     motion_filtered: bool = False) -> dict:
    return insert_record("iot_reading", {
        "user_id": user_id, "metric_type": metric_type,
        "value": value, "ts": ts,
        "threshold_breached": threshold_breached,
        "motion_filtered": motion_filtered,
    })


def get_iot_readings(user_id: str, metric_type: str = None, limit: int = 100) -> list:
    results = query_records("iot_reading", {"user_id": user_id})
    if metric_type:
        results = [r for r in results if r.get("metric_type") == metric_type]
    return results[-limit:]


def save_audit_event(user_id: str, event_type: str,
                     event_hash: str, metadata: dict) -> dict:
    return insert_record("audit_event", {
        "user_id": user_id, "event_type": event_type,
        "event_hash": event_hash, "metadata": metadata,
    })


def get_audit_events(limit: int = 200) -> list:
    return query_records("audit_event")[-limit:]


def save_booking(user_id: str, counselor_id: str,
                 slot_ts: str, anonymous: bool = True) -> dict:
    stored_id = f"anon_{user_id[:8]}" if anonymous else user_id
    return insert_record("booking", {
        "user_id": stored_id, "counselor_id": counselor_id,
        "slot_ts": slot_ts, "status": "pending", "anonymous": anonymous,
    })


def get_bookings(user_id: str) -> list:
    return [b for b in query_records("booking")
            if user_id in b.get("user_id", "")]


def get_aggregate_trends() -> dict:
    screenings = query_records("screening_result")
    mood_logs  = query_records("mood_log")
    alerts     = query_records("audit_event")

    severity_dist: dict = {}
    test_dist:     dict = {}
    for s in screenings:
        sev  = s.get("severity", "unknown")
        test = s.get("test_name", "unknown")
        severity_dist[sev]  = severity_dist.get(sev, 0)  + 1
        test_dist[test]     = test_dist.get(test, 0)     + 1

    avg_mood = (sum(m.get("mood_score", 5) for m in mood_logs) / len(mood_logs)
                if mood_logs else 0.0)
    return {
        "total_screenings":        len(screenings),
        "severity_distribution":   severity_dist,
        "test_distribution":       test_dist,
        "total_mood_logs":         len(mood_logs),
        "average_mood_score":      round(avg_mood, 2),
        "total_escalation_events": len([a for a in alerts
                                        if "crisis" in a.get("event_type","").lower()]),
        "total_iot_alerts":        len([r for r in query_records("iot_reading")
                                        if r.get("threshold_breached")]),
    }


def get_supabase_setup_sql() -> str:
    """
    Returns the SQL to run in Supabase SQL Editor to create the required table.
    Mode 2: Run this once in your Supabase project → SQL Editor.
    """
    return """
-- SentinelMind v5: Single-table architecture for simplicity
-- Run this in Supabase SQL Editor before starting the app in Mode 2

CREATE TABLE IF NOT EXISTS sentinel_records (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    record_type  TEXT NOT NULL,
    ts           TIMESTAMPTZ DEFAULT NOW(),
    payload      JSONB NOT NULL DEFAULT '{}'
);

-- Index for fast type queries
CREATE INDEX IF NOT EXISTS idx_record_type ON sentinel_records(record_type);
-- Index for user-specific queries
CREATE INDEX IF NOT EXISTS idx_user_id ON sentinel_records((payload->>'user_id'));
-- Index for timestamp ordering
CREATE INDEX IF NOT EXISTS idx_ts ON sentinel_records(ts DESC);

-- Row Level Security (optional but recommended for production)
ALTER TABLE sentinel_records ENABLE ROW LEVEL SECURITY;

-- Allow service key full access
CREATE POLICY "Service key full access" ON sentinel_records
    USING (true)
    WITH CHECK (true);

COMMENT ON TABLE sentinel_records IS 'SentinelMind v5 unified record store';
"""
