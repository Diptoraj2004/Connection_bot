"""
services/volunteer_manager.py — Peer Volunteer Management System.

FIX: Training level is now persisted as a separate record type and
loaded correctly on restart via _build_volunteer_state().
"""
import uuid
from datetime import datetime
from data.db import insert_record, query_records

_volunteers: dict = {}
_loaded = False


def _build_volunteer_state():
    """
    Reconstruct full volunteer state from DB on startup.
    Replays training updates on top of registrations — restart-safe.
    """
    global _loaded
    if _loaded:
        return
    # Load base registrations
    for v in query_records("volunteer_registration"):
        _volunteers[v["volunteer_id"]] = dict(v)

    # Replay training updates (latest wins per volunteer)
    for upd in query_records("volunteer_training_update"):
        vid = upd.get("volunteer_id")
        if vid and vid in _volunteers:
            _volunteers[vid]["training_level"] = upd["training_level"]
            _volunteers[vid]["status"] = (
                "active" if upd["training_level"] >= 1 else "pending_training"
            )
    # Replay assignment counts
    active_asgns: dict = {}
    for asgn in query_records("volunteer_assignment"):
        if asgn.get("status") == "active":
            vid = asgn.get("volunteer_id", "")
            active_asgns[vid] = active_asgns.get(vid, 0) + 1
    for vid, count in active_asgns.items():
        if vid in _volunteers:
            _volunteers[vid]["active_assignments"] = count

    _loaded = True


def register_volunteer(name_anon: str, college: str, languages: list,
                       availability_hours: list, email_hash: str = "") -> dict:
    _build_volunteer_state()
    vid = "vol_" + str(uuid.uuid4())[:8]
    record = {
        "volunteer_id":        vid,
        "name_anon":           name_anon,
        "college":             college,
        "languages":           languages,
        "availability_hours":  availability_hours,
        "email_hash":          email_hash,
        "training_level":      0,
        "active_assignments":  0,
        "max_assignments":     2,
        "status":              "pending_training",
        "total_sessions":      0,
        "rating":              None,
        "registered_at":       datetime.utcnow().isoformat(),
    }
    _volunteers[vid] = record
    insert_record("volunteer_registration", record)
    return record


def update_training(volunteer_id: str, level: int) -> dict:
    _build_volunteer_state()
    vol = _volunteers.get(volunteer_id)
    if not vol:
        return {"error": "Volunteer not found"}
    level = min(max(level, 0), 3)
    vol["training_level"] = level
    vol["status"] = "active" if level >= 1 else "pending_training"
    # Persist as a separate record so replays work on restart
    insert_record("volunteer_training_update", {
        "volunteer_id":   volunteer_id,
        "training_level": level,
        "ts":             datetime.utcnow().isoformat(),
    })
    return vol


def assign_volunteer(user_id: str, urgency: str = "standard",
                     preferred_language: str = "English",
                     current_hour: int = None) -> dict | None:
    _build_volunteer_state()
    hour      = current_hour if current_hour is not None else datetime.utcnow().hour
    min_train = 2 if urgency == "crisis" else 1

    candidates = []
    for vol in _volunteers.values():
        if vol["status"] != "active":                              continue
        if vol["training_level"] < min_train:                     continue
        if vol["active_assignments"] >= vol["max_assignments"]:   continue
        if hour not in vol.get("availability_hours", list(range(24))): continue
        score  = (3 if preferred_language in vol.get("languages", []) else 0)
        score += vol["training_level"] - vol["active_assignments"]
        candidates.append((score, vol))

    if not candidates:
        return None

    candidates.sort(key=lambda x: -x[0])
    chosen = candidates[0][1]
    asgn_id = "asgn_" + str(uuid.uuid4())[:8]

    assignment = {
        "assignment_id": asgn_id,
        "volunteer_id":  chosen["volunteer_id"],
        "user_id":       user_id,
        "urgency":       urgency,
        "status":        "active",
        "assigned_at":   datetime.utcnow().isoformat(),
    }
    chosen["active_assignments"] += 1
    insert_record("volunteer_assignment", assignment)
    print(f"[VOLUNTEER] Assigned {chosen['name_anon']} to {user_id}")
    return {**chosen, "assignment_id": asgn_id}


def complete_assignment(assignment_id: str, volunteer_id: str, outcome: str) -> dict:
    _build_volunteer_state()
    vol = _volunteers.get(volunteer_id)
    if vol:
        vol["active_assignments"] = max(0, vol["active_assignments"] - 1)
        vol["total_sessions"]    += 1
    insert_record("volunteer_assignment_complete", {
        "assignment_id": assignment_id,
        "volunteer_id":  volunteer_id,
        "outcome":       outcome,
        "completed_at":  datetime.utcnow().isoformat(),
    })
    return {"status": "completed", "assignment_id": assignment_id}


def get_volunteer_load() -> list:
    _build_volunteer_state()
    return [{"volunteer_id": v["volunteer_id"], "name_anon": v["name_anon"],
             "active": v["active_assignments"], "max": v["max_assignments"],
             "training_level": v["training_level"],
             "training_label": {0:"Unverified",1:"Basic",2:"Intermediate",3:"Advanced"
                                }.get(v["training_level"],"?"),
             "status": v["status"]}
            for v in _volunteers.values()]


def get_available_count(urgency: str = "standard") -> int:
    _build_volunteer_state()
    min_t = 2 if urgency == "crisis" else 1
    return sum(1 for v in _volunteers.values()
               if v["status"] == "active"
               and v["training_level"] >= min_t
               and v["active_assignments"] < v["max_assignments"])
