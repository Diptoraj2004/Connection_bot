"""
services/reminder_engine.py — Follow-up, Inactivity & Academic Risk Engine.

Three jobs:
  1. POST-ESCALATION FOLLOW-UP: If a student had an escalation and hasn't
     returned to the app in N hours, send a check-in message.

  2. INACTIVITY DETECTION: If a previously active student goes silent for
     N days, flag for a gentle outreach.

  3. ACADEMIC RISK WINDOWS: During exam periods / results days / admission
     season, automatically raise monitoring sensitivity for all active users.

All three feed into the escalation chain (quietly — L1 WATCH level)
and can trigger WhatsApp outreach if enabled.
"""

from datetime import datetime, date, timedelta
from config import settings
from data.db import insert_record, query_records, get_mood_logs, get_iot_readings


# ─────────────────────────────────────────────────────────────────────────────
# 1. POST-ESCALATION FOLLOW-UP
# ─────────────────────────────────────────────────────────────────────────────

def check_post_escalation_followups() -> list[dict]:
    """
    Find students who had an escalation event but haven't sent a chat message
    since then. Returns list of users needing a follow-up.
    """
    hours   = settings.followup_reminder_hours
    cutoff  = datetime.utcnow() - timedelta(hours=hours)

    escalations = query_records("escalation_event")
    chat_msgs   = query_records("chat_message")

    # Index latest chat ts per user
    last_chat: dict[str, datetime] = {}
    for msg in chat_msgs:
        uid = msg.get("user_id", "")
        ts_str = msg.get("_ts", "")
        try:
            ts = datetime.fromisoformat(ts_str)
            if uid not in last_chat or ts > last_chat[uid]:
                last_chat[uid] = ts
        except ValueError:
            pass

    overdue = []
    seen_users = set()
    for evt in escalations:
        uid    = evt.get("user_id", "")
        status = evt.get("status", "")
        ts_str = evt.get("_ts", "")

        if uid in seen_users or status == "RESOLVED":
            continue

        try:
            evt_ts = datetime.fromisoformat(ts_str)
        except ValueError:
            continue

        if evt_ts < cutoff:
            last_return = last_chat.get(uid)
            if last_return is None or last_return < evt_ts:
                overdue.append({
                    "user_id":       uid,
                    "event_type":    evt.get("event_type", ""),
                    "escalation_ts": ts_str,
                    "hours_since":   round((datetime.utcnow() - evt_ts).total_seconds() / 3600, 1),
                })
                seen_users.add(uid)

    return overdue


def send_followup_message(user_id: str, hours_since: float) -> str:
    """Generate an appropriate follow-up message based on time elapsed."""
    if hours_since < 24:
        return (
            "Hey — I just wanted to check in. We spoke earlier and I've been thinking about you. "
            "How are you doing right now? 🌱"
        )
    elif hours_since < 72:
        return (
            "It's been a day or two since we talked. I'm here whenever you're ready — "
            "no pressure at all. Just wanted you to know I haven't forgotten about you. 💙"
        )
    else:
        return (
            "I've been thinking about you. It's been a while since we last spoke, "
            "and I just wanted to check that you're okay. "
            "You can always come back here whenever you need — I'll be here. 🌱"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 2. INACTIVITY DETECTION
# ─────────────────────────────────────────────────────────────────────────────

def detect_inactive_users(min_prior_sessions: int = 3) -> list[dict]:
    """
    Find users who were active (≥ min_prior_sessions messages) but have gone
    silent for settings.inactivity_alert_days days.
    """
    threshold_days = settings.inactivity_alert_days
    cutoff         = datetime.utcnow() - timedelta(days=threshold_days)

    all_messages = query_records("chat_message")

    # Group messages by user
    user_msgs: dict[str, list[datetime]] = {}
    for msg in all_messages:
        if msg.get("role") != "user":
            continue
        uid = msg.get("user_id", "")
        ts_str = msg.get("_ts", "")
        try:
            ts = datetime.fromisoformat(ts_str)
            user_msgs.setdefault(uid, []).append(ts)
        except ValueError:
            pass

    inactive = []
    for uid, timestamps in user_msgs.items():
        if len(timestamps) < min_prior_sessions:
            continue  # Not enough prior engagement to flag

        latest = max(timestamps)
        if latest < cutoff:
            days_silent = (datetime.utcnow() - latest).days
            inactive.append({
                "user_id":       uid,
                "total_messages":len(timestamps),
                "last_active":   latest.isoformat(),
                "days_silent":   days_silent,
                "risk":          "moderate" if days_silent < 14 else "high",
            })

    return sorted(inactive, key=lambda x: x["days_silent"], reverse=True)


# ─────────────────────────────────────────────────────────────────────────────
# 3. ACADEMIC RISK WINDOWS
# ─────────────────────────────────────────────────────────────────────────────

def get_current_risk_window() -> dict | None:
    """
    Check if today falls within a configured high-risk academic period.
    Returns the matching window config or None.
    """
    today    = date.today()
    year     = today.year
    mmdd     = today.strftime("%m-%d")

    for window in settings.academic_risk_windows:
        start = window["start"]
        end   = window["end"]

        # Handle year-spanning windows (e.g. Dec–Jan)
        if start > end:
            in_window = mmdd >= start or mmdd <= end
        else:
            in_window = start <= mmdd <= end

        if in_window:
            return {
                "active":      True,
                "window_name": window["name"],
                "start":       start,
                "end":         end,
                "guidance":    (
                    f"We're currently in a high-stress academic period "
                    f"({window['name']}). Monitoring sensitivity is increased. "
                    f"This is one of the highest-risk times of year for student wellbeing."
                ),
            }
    return None


def get_risk_window_message() -> str | None:
    """
    Return a gentle awareness message to show students during risk windows.
    Returns None outside risk windows.
    """
    window = get_current_risk_window()
    if not window:
        return None

    return (
        f"📅 It's {window['window_name']} — one of the most stressful times of year for students. "
        f"It's completely normal to feel overwhelmed right now. "
        f"I'm here, and so is our peer support team. "
        f"You don't have to handle this alone."
    )


# ─────────────────────────────────────────────────────────────────────────────
# 4. SCHEDULED JOB RUNNER (call this from a periodic task or Colab loop)
# ─────────────────────────────────────────────────────────────────────────────

def run_all_checks() -> dict:
    """
    Run all reminder checks. In production: call from a cron/APScheduler job.
    In Colab: call manually every hour or set up a background thread.
    Returns a summary of actions taken.
    """
    summary = {
        "followups_needed":   [],
        "inactive_users":     [],
        "risk_window":        None,
        "escalations_overdue":[],
    }

    # Post-escalation follow-ups
    try:
        followups = check_post_escalation_followups()
        summary["followups_needed"] = followups
        for fu in followups:
            msg = send_followup_message(fu["user_id"], fu["hours_since"])
            print(f"[REMINDER] 📩 Follow-up queued for {fu['user_id']}: {msg[:60]}...")
            insert_record("reminder_sent", {
                "user_id":  fu["user_id"],
                "type":     "post_escalation_followup",
                "message":  msg,
                "trigger":  fu,
            })
    except Exception as e:
        print(f"[REMINDER] Follow-up error: {e}")

    # Inactivity
    try:
        inactive = detect_inactive_users()
        summary["inactive_users"] = inactive
        for user in inactive:
            if user["risk"] == "high":
                # Trigger L1 WATCH escalation
                try:
                    from core.escalation_chain import trigger_escalation
                    trigger_escalation(
                        user_id=user["user_id"],
                        trigger_type="INACTIVITY_DETECTED",
                        details=user,
                        override_level="L1_WATCH",
                    )
                except Exception:
                    pass
    except Exception as e:
        print(f"[REMINDER] Inactivity error: {e}")

    # Academic risk window
    try:
        window = get_current_risk_window()
        summary["risk_window"] = window
        if window:
            print(f"[REMINDER] 📅 Active risk window: {window['window_name']}")
    except Exception as e:
        print(f"[REMINDER] Risk window error: {e}")

    # Overdue escalations
    try:
        from core.escalation_chain import auto_escalate_overdue, check_unacknowledged_events
        overdue = check_unacknowledged_events()
        summary["escalations_overdue"] = overdue
        if overdue:
            auto_escalate_overdue()
    except Exception as e:
        print(f"[REMINDER] Escalation check error: {e}")

    return summary
