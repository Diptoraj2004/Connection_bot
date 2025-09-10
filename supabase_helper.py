# supabase_helper.py
# Supabase helpers with robust local JSON fallback.
# Adds user/account helpers, mood/sleep, alerts, IoT ingestion, and simple auth.

import os
import json
import hashlib
from datetime import datetime, timezone
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_KEY, TABLE_RESPONSES, TABLE_PROGRESS, LOCAL_SAVE_PATH, USER_ID

# Ensure local path directory exists
if LOCAL_SAVE_PATH and os.path.dirname(LOCAL_SAVE_PATH):
    os.makedirs(os.path.dirname(LOCAL_SAVE_PATH), exist_ok=True)


def get_sb_client():
    """Return a Supabase client or None on failure."""
    try:
        if SUPABASE_URL and SUPABASE_KEY:
            return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print("⚠️ Supabase client creation failed:", e)
    return None


# -----------------------------
# Local JSON helpers
# -----------------------------
def _read_local():
    data = {}
    try:
        if os.path.exists(LOCAL_SAVE_PATH):
            with open(LOCAL_SAVE_PATH, "r", encoding="utf-8") as fh:
                data = json.load(fh)
    except Exception:
        data = {}
    return data


def _write_local(data):
    try:
        with open(LOCAL_SAVE_PATH, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
    except Exception as e:
        print("⚠️ Failed writing local save:", e)


# -----------------------------
# Responses
# -----------------------------
def insert_response(user_id, question_id, question, answer):
    """
    Insert/upsert a response row in Supabase; fallback to local JSON.
    Expected Supabase table columns: user_id, question_id, question, answer, ts
    """
    row = {
        "user_id": user_id,
        "question_id": question_id,
        "question": question,
        "answer": answer,
        "ts": datetime.now(timezone.utc).isoformat()
    }
    try:
        sb = get_sb_client()
        if sb:
            sb.table(TABLE_RESPONSES).upsert(row).execute()
            return
    except Exception as e:
        print("⚠️ Supabase responses insert failed, falling back to local JSON:", e)

    data = _read_local()
    data.setdefault(user_id, {}).setdefault("responses", []).append(row)
    _write_local(data)


# Backwards-compatible wrapper name used across versions
def upsert_response_supabase(sb_client, user_id, question, answer):
    qid = (question or "")[:16]
    insert_response(user_id, qid, question, answer)


# -----------------------------
# Progress
# -----------------------------
def save_progress(user_id, batch_index):
    row = {"user_id": user_id, "current_batch": int(batch_index), "updated_at": datetime.now(timezone.utc).isoformat()}
    try:
        sb = get_sb_client()
        if sb:
            sb.table(TABLE_PROGRESS).upsert(row).execute()
    except Exception as e:
        print("⚠️ Supabase save_progress failed, falling back to local JSON:", e)

    data = _read_local()
    data.setdefault(user_id, {})["current_batch"] = int(batch_index)
    _write_local(data)


def load_progress(user_id):
    try:
        sb = get_sb_client()
        if sb:
            res = sb.table(TABLE_PROGRESS).select("*").eq("user_id", user_id).limit(1).execute()
            if getattr(res, "data", None):
                return int(res.data[0].get("current_batch", 1))
    except Exception:
        pass
    data = _read_local()
    return int(data.get(user_id, {}).get("current_batch", 1))


# -----------------------------
# Mood Logs
# -----------------------------
def insert_mood(user_id, rating, note=None):
    row = {"user_id": user_id, "rating": rating, "note": note, "ts": datetime.now(timezone.utc).isoformat()}
    try:
        sb = get_sb_client()
        if sb:
            sb.table("mood_logs").insert(row).execute()
            return
    except Exception as e:
        print("⚠️ Supabase mood insert failed, fallback to local JSON:", e)

    data = _read_local()
    data.setdefault(user_id, {}).setdefault("mood_log", []).append(row)
    _write_local(data)


# -----------------------------
# Sleep Logs
# -----------------------------
def insert_sleep(user_id, duration_hours, quality=None):
    row = {"user_id": user_id, "duration_hours": duration_hours, "quality": quality, "ts": datetime.now(timezone.utc).isoformat()}
    try:
        sb = get_sb_client()
        if sb:
            sb.table("sleep_logs").insert(row).execute()
            return
    except Exception as e:
        print("⚠️ Supabase sleep insert failed, fallback to local JSON:", e)

    data = _read_local()
    data.setdefault(user_id, {}).setdefault("sleep_log", []).append(row)
    _write_local(data)


# -----------------------------
# Alerts / Escalations
# -----------------------------
def push_alert(user_id, level, reason, meta=None):
    row = {"user_id": user_id, "level": level, "reason": reason, "meta": meta, "ts": datetime.now(timezone.utc).isoformat()}
    try:
        sb = get_sb_client()
        if sb:
            try:
                sb.table("alerts").insert(row).execute()
            except Exception:
                sb.table("escalations").insert(row).execute()
            return
    except Exception as e:
        print("⚠️ Supabase alert insert failed, fallback to local JSON:", e)

    data = _read_local()
    data.setdefault(user_id, {}).setdefault("alerts", []).append(row)
    _write_local(data)


# -----------------------------
# IoT ingestion / readings
# -----------------------------
def insert_iot_reading(user_id, readings: dict):
    """
    readings: dict like {"sweat":0.3,"spo2":97,"hr":85,"sleep_hours":5.2,"ts":"..."}
    Stores to supabase table 'iot_readings' (if present) or local fallback.
    """
    row = {
        "user_id": user_id,
        "readings": readings,
        "ts": readings.get("ts") or datetime.now(timezone.utc).isoformat()
    }
    try:
        sb = get_sb_client()
        if sb:
            sb.table("iot_readings").insert(row).execute()
            return
    except Exception as e:
        print("⚠️ Supabase iot insert failed, fallback to local JSON:", e)

    data = _read_local()
    data.setdefault(user_id, {}).setdefault("iot_readings", []).append(row)
    _write_local(data)


# -----------------------------
# Simple User / Auth helpers (local-first)
# -----------------------------
def _hash_password(raw: str) -> str:
    return hashlib.sha256((raw or "").encode("utf-8")).hexdigest()


def create_user_if_not_exists(user_id, password=None, name=None, email=None, role="student"):
    """
    Creates a user record in local JSON if not present. If Supabase user table exists you can extend it later.
    Returns the user dict.
    """
    data = _read_local()
    users = data.setdefault("users", {})
    if user_id in users:
        return users[user_id]
    users[user_id] = {
        "user_id": user_id,
        "name": name,
        "email": email,
        "role": role,
        "password_hash": _hash_password(password) if password else None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    _write_local(data)
    return users[user_id]


def authenticate_user(user_id, password) -> bool:
    """
    Very lightweight authentication using local JSON. Returns True if password matches.
    """
    data = _read_local()
    users = data.get("users", {})
    u = users.get(user_id)
    if not u:
        return False
    if not u.get("password_hash"):
        # if no password saved, allow if password is blank (first-time)
        return password == "" or password is None
    return _hash_password(password) == u.get("password_hash")


def get_user_role(user_id):
    data = _read_local()
    users = data.get("users", {})
    u = users.get(user_id, {})
    return u.get("role")


# -----------------------------
# IoT → simple auto-escalation heuristics
# -----------------------------
def evaluate_iot_and_alert(user_id, readings, thresholds=None):
    """
    thresholds example: {"spo2": 92, "hr_max": 140, "sweat": 1.0}
    If any reading exceeds threshold, push alert and return True.
    """
    th = thresholds or {"spo2": 92, "hr_max": 140, "sweat": 1.5, "sleep_hours_min": 3}
    triggered = False
    meta = {}
    try:
        spo2 = float(readings.get("spo2") or 0)
        hr = float(readings.get("hr") or 0)
        sweat = float(readings.get("sweat") or 0)
        sleep_hours = float(readings.get("sleep_hours") or 0)
        if spo2 and spo2 < th["spo2"]:
            meta["spo2"] = spo2
            triggered = True
        if hr and hr > th["hr_max"]:
            meta["hr"] = hr
            triggered = True
        if sweat and sweat > th["sweat"]:
            meta["sweat"] = sweat
            triggered = True
        if sleep_hours and sleep_hours < th["sleep_hours_min"]:
            meta["sleep_hours"] = sleep_hours
            triggered = True
    except Exception:
        pass

    if triggered:
        push_alert(user_id, "high", "iot_threshold", meta=meta)
    return triggered


# ===========================
# End of supabase_helper
# ===========================
