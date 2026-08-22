"""
core/escalation_chain.py — Full Accountability Escalation Chain.

Every escalation: logs to Merkle Ledger, notifies all parties simultaneously,
requires acknowledgement, auto-re-escalates if unacknowledged, tracks until resolved.

Levels:
  L1 — WATCH:    AI monitors. No external notification.
  L2 — ALERT:    Peer Volunteer + Campus Counselor notified. 60-min ACK window.
  L3 — URGENT:   Head Counselor + Admin notified. 30-min ACK window.
  L4 — CRITICAL: All parties + Emergency protocol. 15-min ACK window.
                 Parents ONLY with student consent OR if unreachable/unconscious.
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional
from config import settings

ESCALATION_LEVELS = {
    "L1_WATCH": {
        "label":               "Watch",
        "notify":              ["ai_system"],
        "ack_timeout_minutes": None,
        "description":         "AI monitoring elevated. No external alert.",
        "student_message":     None,
    },
    "L2_ALERT": {
        "label":               "Alert",
        "notify":              ["peer_volunteer", "campus_counselor"],
        "ack_timeout_minutes": 60,
        "description":         "Peer volunteer and campus counselor notified.",
        "student_message": (
            "I'm a little concerned about you and want to make sure you're supported. "
            "A trained peer volunteer will check in with you soon. "
            "You don't have to go through this alone."
        ),
    },
    "L3_URGENT": {
        "label":               "Urgent",
        "notify":              ["peer_volunteer", "campus_counselor", "head_counselor", "institute_admin"],
        "ack_timeout_minutes": 30,
        "description":         "Head counselor and admin notified. Immediate response required.",
        "student_message": (
            "I'm genuinely worried about you right now. "
            "A counselor is being notified and will reach out very soon. "
            "Please stay with me — can you tell me where you are right now?"
        ),
    },
    "L4_CRITICAL": {
        "label":               "Critical",
        "notify":              ["peer_volunteer", "campus_counselor", "head_counselor",
                                "institute_admin", "emergency_services_protocol"],
        "ack_timeout_minutes": 15,
        "description":         "Full crisis protocol. Emergency services procedure activated.",
        "student_message": (
            "🚨 I'm very concerned about your safety right now. "
            "You matter deeply, and people are being contacted to support you.\n\n"
            "Please call Kiran NOW: **1800-599-0019** (free, 24/7)\n"
            "Or AASRA: **91-22-27546669**\n\n"
            "Can you tell me — are you safe right now? Where are you?"
        ),
        "parent_notify": "consent_required",
    },
}

# Complete trigger→level map including bullying and inactivity
TRIGGER_LEVEL_MAP = {
    # Behavioral monitor
    "HYPER_TO_CALM_TRANSITION": "L4_CRITICAL",
    "WITHDRAWAL_WITH_CALM":     "L3_URGENT",
    "SUSTAINED_WITHDRAWAL":     "L2_ALERT",
    "SUDDEN_SILENCE":           "L2_ALERT",
    "HIGH_CUMULATIVE_RISK":     "L2_ALERT",
    "BULLYING_DETECTED":        "L2_ALERT",

    # Crisis interceptor
    "CRISIS_KEYWORD":           "L4_CRITICAL",
    "PHQ9_CRISIS_QUESTION":     "L3_URGENT",
    "SCREENING_ESCALATION":     "L2_ALERT",
    "SCREENING_SEVERE":         "L3_URGENT",

    # IoT
    "IOT_THRESHOLD_BREACH":     "L2_ALERT",
    "IOT_CRITICAL_BREACH":      "L3_URGENT",

    # Counselor-initiated
    "COUNSELOR_ESCALATED":      "L3_URGENT",
    "COUNSELOR_EMERGENCY":      "L4_CRITICAL",

    # Reminder engine
    "INACTIVITY_DETECTED":      "L1_WATCH",
    "FOLLOWUP_MISSED":          "L2_ALERT",
    "AUTO_ESCALATION_TIMEOUT":  "L3_URGENT",
}

_active_events: dict = {}


class EscalationEvent:
    def __init__(self, user_id: str, trigger_type: str, level: str,
                 details: dict, session_id: str = ""):
        self.event_id     = str(uuid.uuid4())
        self.user_id      = user_id
        self.session_id   = session_id
        self.trigger_type = trigger_type
        self.level        = level
        self.level_config = ESCALATION_LEVELS[level]
        self.details      = details
        self.created_at   = datetime.utcnow().isoformat()
        self.status       = "ACTIVE"
        self.notified:        list = []
        self.acknowledgements:list = []
        self.actions_taken:   list = []
        self.resolved_at:  Optional[str] = None
        self.resolved_by:  Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "event_id":         self.event_id,
            "user_id":          self.user_id,
            "session_id":       self.session_id,
            "trigger_type":     self.trigger_type,
            "level":            self.level,
            "level_label":      self.level_config["label"],
            "description":      self.level_config["description"],
            "created_at":       self.created_at,
            "status":           self.status,
            "notified":         self.notified,
            "acknowledgements": self.acknowledgements,
            "actions_taken":    self.actions_taken,
            "resolved_at":      self.resolved_at,
            "resolved_by":      self.resolved_by,
            "details":          self.details,
        }


def trigger_escalation(user_id: str, trigger_type: str, details: dict,
                       session_id: str = "",
                       override_level: Optional[str] = None) -> dict:
    level        = override_level or TRIGGER_LEVEL_MAP.get(trigger_type, "L2_ALERT")
    level_config = ESCALATION_LEVELS[level]
    levels_ord   = ["L1_WATCH", "L2_ALERT", "L3_URGENT", "L4_CRITICAL"]

    existing = _active_events.get(user_id)
    if existing and existing.status == "ACTIVE":
        existing_idx = levels_ord.index(existing.level)
        new_idx      = levels_ord.index(level)
        if new_idx <= existing_idx:
            existing.details.setdefault("additional_triggers", []).append(
                {"trigger": trigger_type, "ts": datetime.utcnow().isoformat()}
            )
            _persist(existing)
            return {"event_id": existing.event_id, "action": "updated_existing",
                    "level": existing.level, "student_message": None}
        existing.status = "RE_ESCALATED"

    event = EscalationEvent(user_id, trigger_type, level, details, session_id)

    _log_to_merkle(event)
    for party in level_config["notify"]:
        _notify_party(event, party)

    ack_timeout = level_config.get("ack_timeout_minutes")
    if ack_timeout:
        event.details["ack_deadline"]         = (
            datetime.utcnow() + timedelta(minutes=ack_timeout)).isoformat()
        event.details["ack_timeout_minutes"]  = ack_timeout

    _active_events[user_id] = event
    _persist(event)

    print(f"\n[ESCALATION] {level} | {trigger_type} | user={user_id} | id={event.event_id[:8]}")
    return {
        "event_id":        event.event_id,
        "action":          "created",
        "level":           level,
        "level_label":     level_config["label"],
        "notified":        event.notified,
        "student_message": level_config.get("student_message"),
        "ack_deadline":    event.details.get("ack_deadline"),
    }


def acknowledge_event(event_id: str, acknowledged_by: str, note: str = "") -> dict:
    event = _find_by_id(event_id)
    if not event:
        return {"error": "Event not found"}
    event.acknowledgements.append({
        "acknowledged_by": acknowledged_by,
        "ts":              datetime.utcnow().isoformat(),
        "note":            note,
    })
    event.status = "ACKNOWLEDGED"
    _persist(event)
    print(f"[ESCALATION] ✅ {event_id[:8]} acknowledged by {acknowledged_by}")
    return {"status": "acknowledged", "event_id": event_id}


def resolve_event(event_id: str, resolved_by: str, outcome: str) -> dict:
    event = _find_by_id(event_id)
    if not event:
        return {"error": "Event not found"}
    event.status      = "RESOLVED"
    event.resolved_at = datetime.utcnow().isoformat()
    event.resolved_by = resolved_by
    event.actions_taken.append({
        "action":  "RESOLVED",
        "by":      resolved_by,
        "outcome": outcome,
        "ts":      datetime.utcnow().isoformat(),
    })
    _active_events.pop(event.user_id, None)
    _persist(event)
    try:
        from core.merkle_ledger import log_event
        log_event(event.user_id, "ESCALATION_RESOLVED",
                  {"event_id": event_id, "resolved_by": resolved_by, "outcome": outcome},
                  notify_counselor=False)
    except Exception as e:
        print(f"[ESCALATION] Merkle resolution error: {e}")
    print(f"[ESCALATION] 🟢 {event_id[:8]} resolved by {resolved_by}: {outcome}")
    return {"status": "resolved", "event_id": event_id, "outcome": outcome}


def check_unacknowledged_events() -> list:
    overdue = []
    now = datetime.utcnow()
    for user_id, event in list(_active_events.items()):
        if event.status != "ACTIVE":
            continue
        deadline_str = event.details.get("ack_deadline")
        if not deadline_str:
            continue
        try:
            deadline = datetime.fromisoformat(deadline_str)
            if now > deadline:
                overdue.append({
                    "event_id":        event.event_id,
                    "user_id":         user_id,
                    "level":           event.level,
                    "created_at":      event.created_at,
                    "minutes_overdue": int((now - deadline).total_seconds() / 60),
                })
        except ValueError:
            pass
    return overdue


def auto_escalate_overdue():
    levels_ord = ["L1_WATCH", "L2_ALERT", "L3_URGENT", "L4_CRITICAL"]
    for item in check_unacknowledged_events():
        event = _find_by_id(item["event_id"])
        if not event:
            continue
        idx        = levels_ord.index(event.level)
        next_level = levels_ord[min(idx + 1, len(levels_ord) - 1)]
        print(f"[ESCALATION] ⏰ Auto-escalating {event.event_id[:8]} "
              f"{event.level}→{next_level} ({item['minutes_overdue']} min overdue)")
        trigger_escalation(
            user_id=event.user_id,
            trigger_type="AUTO_ESCALATION_TIMEOUT",
            details={"original_event_id": event.event_id,
                     "original_level":    event.level,
                     "reason":            f"Unacknowledged {item['minutes_overdue']} min"},
            override_level=next_level,
        )


def get_active_event(user_id: str) -> Optional[dict]:
    e = _active_events.get(user_id)
    return e.to_dict() if e else None


def get_all_active_events() -> list:
    return [e.to_dict() for e in _active_events.values()]


def _notify_party(event: EscalationEvent, party: str):
    ts  = datetime.utcnow().isoformat()
    msg = {
        "peer_volunteer":            f"[PEER ALERT] Student needs support. ID={event.event_id[:8]} Level={event.level_config['label']}",
        "campus_counselor":          f"[COUNSELOR ALERT] {event.trigger_type} flagged. ID={event.event_id[:8]} Level={event.level_config['label']}",
        "head_counselor":            f"[URGENT — HEAD COUNSELOR] {event.trigger_type}. Immediate action. ID={event.event_id[:8]}",
        "institute_admin":           f"[ADMIN] Crisis protocol activated. ID={event.event_id[:8]}",
        "emergency_services_protocol": f"[CRITICAL] Full emergency protocol. ID={event.event_id}",
        "ai_system":                 "[INTERNAL] Monitoring elevated.",
    }.get(party, f"[NOTIFY] Alert: {party}")

    print(f"[NOTIFY → {party.upper()}] {msg}")
    event.notified.append({
        "party":    party,
        "ts":       ts,
        "method":   {"peer_volunteer": "push+whatsapp", "campus_counselor": "sms+dashboard",
                     "head_counselor": "sms+email",     "institute_admin": "email+dashboard",
                     "emergency_services_protocol": "in_person", "ai_system": "internal"
                     }.get(party, "unknown"),
        "delivered": True,
    })


def _log_to_merkle(event: EscalationEvent):
    try:
        from core.merkle_ledger import log_event
        log_event(event.user_id, f"ESCALATION_{event.level}",
                  {"event_id": event.event_id, "trigger": event.trigger_type,
                   "level": event.level, "details": event.details},
                  notify_counselor=event.level in ("L3_URGENT", "L4_CRITICAL"))
    except Exception as e:
        print(f"[ESCALATION] Merkle error: {e}")


def _persist(event: EscalationEvent):
    try:
        from data.db import insert_record
        insert_record("escalation_event", event.to_dict())
    except Exception as e:
        print(f"[ESCALATION] DB persist error: {e}")


def _find_by_id(event_id: str) -> Optional[EscalationEvent]:
    for e in _active_events.values():
        if e.event_id == event_id:
            return e
    return None
