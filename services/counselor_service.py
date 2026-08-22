"""
services/counselor_service.py — Counselor Management, Session Notes & Capacity.

FIX: _csl_loaded flag prevents empty-dict fooling the load guard.
FIX: counselor_registration record type used consistently.
FIX: current_students persisted across restarts via counselor_state records.
"""
import uuid
from datetime import datetime
from data.db import insert_record, query_records

_counselors: dict = {}
_csl_loaded: bool = False


def _load():
    """Load counselors from DB. _csl_loaded prevents empty-dict guard failure."""
    global _csl_loaded
    if _csl_loaded:
        return
    for c in query_records("counselor_registration"):
        cid = c.get("counselor_id")
        if cid:
            _counselors[cid] = dict(c)
    # Replay latest student count from state records
    for s in query_records("counselor_state"):
        cid = s.get("counselor_id")
        if cid and cid in _counselors:
            _counselors[cid]["current_students"] = s.get("current_students", 0)
    _csl_loaded = True


def _persist_counselor(counselor_id: str):
    """Persist current_students count so it survives restarts."""
    c = _counselors.get(counselor_id)
    if c:
        insert_record("counselor_state", {
            "counselor_id":    counselor_id,
            "current_students":c.get("current_students", 0),
            "ts":              datetime.utcnow().isoformat(),
        })


def register_counselor(name: str, email_hash: str, college: str,
                       specialties: list, languages: list,
                       max_students: int = 30) -> dict:
    _load()
    cid = "csl_" + str(uuid.uuid4())[:8]
    record = {
        "counselor_id":     cid,
        "name":             name,
        "email_hash":       email_hash,
        "college":          college,
        "specialties":      specialties,
        "languages":        languages,
        "max_students":     max_students,
        "current_students": 0,
        "status":           "active",
        "registered_at":    datetime.utcnow().isoformat(),
    }
    _counselors[cid] = record
    insert_record("counselor_registration", record)
    return record


def get_counselor_capacity() -> list:
    _load()
    result = []
    for c in _counselors.values():
        load_pct = (c["current_students"] / max(c["max_students"], 1)) * 100
        result.append({
            "counselor_id":    c["counselor_id"],
            "name":            c["name"],
            "current_students":c["current_students"],
            "max_students":    c["max_students"],
            "load_percent":    round(load_pct, 1),
            "available":       c["current_students"] < c["max_students"],
            "status":          c["status"],
        })
    return sorted(result, key=lambda x: x["load_percent"])


def get_least_loaded_counselor(specialty: str = "") -> dict | None:
    _load()
    candidates = []
    for c in _counselors.values():
        if c["status"] != "active":
            continue
        if c["current_students"] >= c["max_students"]:
            continue
        score = 0
        if specialty and specialty in c.get("specialties", []):
            score += 2
        score -= c["current_students"]
        candidates.append((score, c))
    if not candidates:
        return None
    candidates.sort(key=lambda x: -x[0])
    return candidates[0][1]


def assign_student_to_counselor(counselor_id: str) -> bool:
    """Increment student count and persist."""
    _load()
    c = _counselors.get(counselor_id)
    if not c:
        return False
    c["current_students"] += 1
    _persist_counselor(counselor_id)
    return True


def create_session_note(counselor_id: str, user_id_hash: str,
                        session_date: str, session_type: str,
                        presenting_issues: list, interventions: list,
                        risk_level: str, next_appointment: str,
                        private_notes: str, shared_summary: str) -> dict:
    note = {
        "note_id":           "note_" + str(uuid.uuid4())[:8],
        "counselor_id":      counselor_id,
        "user_id_hash":      user_id_hash,
        "session_date":      session_date,
        "session_type":      session_type,
        "presenting_issues": presenting_issues,
        "interventions":     interventions,
        "risk_level":        risk_level,
        "next_appointment":  next_appointment,
        "private_notes":     private_notes,
        "shared_summary":    shared_summary,
        "created_at":        datetime.utcnow().isoformat(),
    }
    insert_record("session_note", note)

    if risk_level in ("high", "critical"):
        try:
            from core.escalation_chain import trigger_escalation
            trigger_escalation(
                user_id=user_id_hash,
                trigger_type="COUNSELOR_ESCALATED",
                details={"risk_level": risk_level, "counselor_id": counselor_id,
                         "note_id": note["note_id"]},
                override_level="L3_URGENT" if risk_level == "high" else "L4_CRITICAL",
            )
        except Exception as e:
            print(f"[COUNSELOR] Escalation error: {e}")
    return note


def get_session_notes(counselor_id: str, user_id_hash: str = None) -> list:
    notes = query_records("session_note", {"counselor_id": counselor_id})
    if user_id_hash:
        notes = [n for n in notes if n.get("user_id_hash") == user_id_hash]
    return notes


def get_counselor_student_roster(counselor_id: str) -> list:
    bookings = query_records("booking")
    return [b for b in bookings
            if b.get("counselor_id") == counselor_id
            and b.get("status") != "completed"]


def get_aggregate_session_stats() -> dict:
    notes = query_records("session_note")
    if not notes:
        return {"total": 0}
    risk_dist: dict = {}
    type_dist: dict = {}
    issue_freq: dict = {}
    for n in notes:
        r = n.get("risk_level", "unknown")
        t = n.get("session_type", "unknown")
        risk_dist[r] = risk_dist.get(r, 0) + 1
        type_dist[t] = type_dist.get(t, 0) + 1
        for issue in n.get("presenting_issues", []):
            issue_freq[issue] = issue_freq.get(issue, 0) + 1
    return {
        "total":             len(notes),
        "risk_distribution": risk_dist,
        "type_distribution": type_dist,
        "top_issues":        sorted(issue_freq.items(), key=lambda x: -x[1])[:10],
    }
