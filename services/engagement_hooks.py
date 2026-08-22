"""
services/engagement_hooks.py — Non-Clinical Engagement Features.

POINT 3 of 7: Entry points that generate passive data without clinical framing.

THE PROBLEM: Students won't open a "mental health app." They will open a
study tracker, a sleep challenge, or a music mood journal.

These hooks generate the same passive signals the clinical system needs,
but the student engages because of immediate personal value — not therapy.

FEATURES:
  1. STUDY TRACKER     — Pomodoro sessions, focus scores, streak gamification
  2. SLEEP CHALLENGE   — Hostel-block sleep leaderboard, streak badges
  3. MUSIC MOOD JOURNAL— What are you listening to? Spotify/JioSaavn proxy
  4. ACADEMIC CALENDAR — Exam dates → auto-heightened monitoring windows
  5. CAMPUS FRIEND PING— Anonymous peer check-ins ("your friend seems low")
"""
from datetime import datetime, date, timedelta
from data.db import insert_record, query_records, get_latest
from config import settings


# ─────────────────────────────────────────────────────────────────────────────
# 1. STUDY TRACKER
# ─────────────────────────────────────────────────────────────────────────────

def log_study_session(user_id: str, duration_minutes: int,
                      subject: str = "", focus_self_rating: int = 5,
                      interruptions: int = 0) -> dict:
    """
    Log a Pomodoro/study session. Students get points and see focus trends.
    Passive signals: session time (late night = sleep disruption),
    focus rating trend (dropping focus = early distress signal).
    """
    hour_of_day = datetime.utcnow().hour

    # Passive signal: studying at 2-5am
    late_night = 2 <= hour_of_day <= 5
    if late_night:
        _flag_passive_signal(user_id, "late_night_studying", {
            "hour": hour_of_day, "subject": subject,
            "note": "Studying at unusual hours — possible sleep disruption or academic stress"
        })

    # Focus score: weighted average of self-rating and interruption frequency
    interruption_penalty = min(interruptions * 5, 40)
    focus_score = max(0, min(100, (focus_self_rating * 10) - interruption_penalty))

    record = insert_record("study_session", {
        "user_id":          user_id,
        "duration_minutes": duration_minutes,
        "subject":          subject,
        "focus_score":      focus_score,
        "interruptions":    interruptions,
        "hour_of_day":      hour_of_day,
        "late_night":       late_night,
        "date":             date.today().isoformat(),
    })

    # Check focus trend — dropping focus over 5+ sessions is early distress signal
    trend = _get_focus_trend(user_id)
    if trend["declining"] and trend["sessions"] >= 5:
        _flag_passive_signal(user_id, "declining_focus_trend", {
            "recent_avg": trend["recent_avg"],
            "previous_avg": trend["previous_avg"],
            "note": "Consistent focus decline may indicate academic stress or mood change"
        })

    # Award points
    from data.progress_store import update_progress
    progress = update_progress(user_id, 6, events=["study_session"])

    return {
        "status":       "logged",
        "focus_score":  focus_score,
        "duration_min": duration_minutes,
        "late_night":   late_night,
        "progress":     progress,
        "trend":        trend,
        "tip":          _study_tip(focus_score, late_night),
    }


def get_study_stats(user_id: str, days: int = 7) -> dict:
    """Study stats for the student dashboard."""
    cutoff   = (date.today() - timedelta(days=days)).isoformat()
    sessions = [s for s in query_records("study_session", {"user_id": user_id})
                if s.get("date", "") >= cutoff]
    if not sessions:
        return {"total_minutes": 0, "sessions": 0, "avg_focus": 0, "trend": "no_data"}

    total_mins = sum(s.get("duration_minutes", 0) for s in sessions)
    avg_focus  = sum(s.get("focus_score", 0) for s in sessions) / len(sessions)
    late_count = sum(1 for s in sessions if s.get("late_night"))

    return {
        "total_minutes":     total_mins,
        "total_hours":       round(total_mins / 60, 1),
        "sessions":          len(sessions),
        "avg_focus_score":   round(avg_focus, 1),
        "late_night_sessions": late_count,
        "streak":            _study_streak(user_id),
        "subjects":          list({s.get("subject","") for s in sessions if s.get("subject")}),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2. SLEEP CHALLENGE
# ─────────────────────────────────────────────────────────────────────────────

def log_sleep(user_id: str, sleep_hours: float, sleep_quality: int,
              bedtime_hour: int, wake_hour: int,
              college_id: str = "default") -> dict:
    """
    Log sleep data. Returns personalized feedback + anonymous hostel comparison.
    Passive signal: chronic short sleep (<6h) or irregular timing.
    """
    insert_record("sleep_log", {
        "user_id":       user_id,
        "sleep_hours":   sleep_hours,
        "sleep_quality": sleep_quality,  # 1-10
        "bedtime_hour":  bedtime_hour,
        "wake_hour":     wake_hour,
        "college_id":    college_id,
        "date":          date.today().isoformat(),
    })

    # Also feed into IoT adapter if wearable not connected
    from services.iot_adapter import process_reading
    process_reading(user_id, "sleep_hours", sleep_hours)

    # Passive: chronic poor sleep
    recent_logs = query_records("sleep_log", {"user_id": user_id})[-7:]
    if len(recent_logs) >= 5:
        avg_sleep = sum(s.get("sleep_hours", 7) for s in recent_logs) / len(recent_logs)
        if avg_sleep < 6.0:
            _flag_passive_signal(user_id, "chronic_sleep_deficit", {
                "7day_avg_hours": round(avg_sleep, 1),
                "note": "Chronic sleep deprivation amplifies depression/anxiety by 3-4x"
            })

    # Anonymous hostel comparison (motivational, not clinical)
    college_avg = _get_college_sleep_avg(college_id)
    badge = _sleep_badge(sleep_hours)

    from data.progress_store import update_progress
    progress = update_progress(user_id, sleep_quality, events=["sleep_log"])

    return {
        "status":        "logged",
        "sleep_hours":   sleep_hours,
        "quality_score": sleep_quality,
        "badge":         badge,
        "college_avg":   college_avg,
        "comparison":    _sleep_comparison(sleep_hours, college_avg),
        "progress":      progress,
        "tip":           _sleep_tip(sleep_hours, bedtime_hour),
    }


def get_sleep_leaderboard(college_id: str = "default", days: int = 7) -> list:
    """
    Anonymous sleep leaderboard for hostel/college — motivational peer comparison.
    No names or IDs — only anonymous badges.
    """
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    logs   = [s for s in query_records("sleep_log", {"college_id": college_id})
              if s.get("date","") >= cutoff]

    user_avgs: dict = {}
    for log in logs:
        uid = log.get("user_id","")
        if uid not in user_avgs:
            user_avgs[uid] = []
        user_avgs[uid].append(log.get("sleep_hours", 0))

    ranked = sorted(
        [{"rank": 0, "badge": _sleep_badge(sum(v)/len(v)),
          "avg_hours": round(sum(v)/len(v), 1), "days": len(v)}
         for v in user_avgs.values()],
        key=lambda x: -x["avg_hours"]
    )
    for i, r in enumerate(ranked):
        r["rank"] = i + 1
    return ranked[:20]


# ─────────────────────────────────────────────────────────────────────────────
# 3. MUSIC MOOD JOURNAL
# ─────────────────────────────────────────────────────────────────────────────

MOOD_MUSIC_PROXY = {
    # Genre → likely mood signal
    "sad":      ["slow", "minor", "ballad", "arijit", "melancholy", "breakup", "lofi"],
    "anxious":  ["fast", "intense", "metal", "aggressive", "upbeat_forced"],
    "happy":    ["dance", "pop", "party", "upbeat", "bollywood_dance"],
    "depressed":["repetitive", "dark", "numb", "silent", "ambient_dark"],
    "focused":  ["instrumental", "classical", "binaural", "lo-fi study"],
    "nostalgic":["old", "retro", "90s", "childhood", "memory"],
}


def log_music_mood(user_id: str, track_name: str, artist: str,
                   genre_tags: list, self_mood: str = "") -> dict:
    """
    Log what the student is listening to. No Spotify API needed —
    student just types the song name. Optional self-mood label.
    Passive signal: music genre is a known mood proxy.
    """
    # Infer mood from genre tags
    inferred_mood = _infer_mood_from_music(genre_tags, track_name.lower())

    insert_record("music_mood_log", {
        "user_id":      user_id,
        "track":        track_name,
        "artist":       artist,
        "genre_tags":   genre_tags,
        "inferred_mood":inferred_mood,
        "self_mood":    self_mood,
        "date":         date.today().isoformat(),
        "hour":         datetime.utcnow().hour,
    })

    # If consistently logging sad/depressed music
    recent = query_records("music_mood_log", {"user_id": user_id})[-7:]
    sad_count = sum(1 for m in recent if m.get("inferred_mood") in ("sad","depressed"))
    if sad_count >= 5 and len(recent) >= 5:
        _flag_passive_signal(user_id, "persistent_sad_music_pattern", {
            "sad_logs": sad_count,
            "total_logs": len(recent),
            "note": "5+ days of sad/melancholic music may indicate low mood"
        })

    return {
        "logged":         True,
        "inferred_mood":  inferred_mood,
        "recommendation": _get_mood_nudge(inferred_mood),
    }


def get_music_mood_trend(user_id: str, days: int = 14) -> dict:
    """Music mood trend for student dashboard."""
    cutoff = (date.today() - timedelta(days=days)).isoformat()
    logs   = [m for m in query_records("music_mood_log", {"user_id": user_id})
              if m.get("date","") >= cutoff]
    if not logs:
        return {"trend": "no_data", "dominant_mood": None}

    from collections import Counter
    mood_counts = Counter(m.get("inferred_mood","neutral") for m in logs)
    dominant    = mood_counts.most_common(1)[0][0]

    return {
        "dominant_mood":  dominant,
        "mood_breakdown": dict(mood_counts),
        "total_logs":     len(logs),
        "trend_note":     f"Your music mostly reflects a '{dominant}' mood lately.",
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4. ACADEMIC CALENDAR
# ─────────────────────────────────────────────────────────────────────────────

def add_exam_date(user_id: str, subject: str, exam_date: str,
                  exam_type: str = "semester") -> dict:
    """
    Student adds their own exam dates.
    System auto-elevates monitoring sensitivity 7 days before each exam.
    """
    insert_record("exam_calendar", {
        "user_id":    user_id,
        "subject":    subject,
        "exam_date":  exam_date,
        "exam_type":  exam_type,
        "added_at":   datetime.utcnow().isoformat(),
    })
    return {
        "status":  "added",
        "subject": subject,
        "date":    exam_date,
        "note":    f"I'll check in with you more often as {exam_date} approaches.",
    }


def get_upcoming_exams(user_id: str) -> list:
    """Get upcoming exams and their monitoring status."""
    today     = date.today()
    all_exams = query_records("exam_calendar", {"user_id": user_id})
    upcoming  = []
    for exam in all_exams:
        try:
            exam_dt  = date.fromisoformat(exam.get("exam_date",""))
            days_left= (exam_dt - today).days
            if days_left >= 0:
                upcoming.append({
                    "subject":         exam.get("subject",""),
                    "date":            exam.get("exam_date",""),
                    "days_remaining":  days_left,
                    "monitoring_elevated": days_left <= 7,
                    "stress_window":   days_left <= 3,
                })
        except ValueError:
            pass
    return sorted(upcoming, key=lambda x: x["days_remaining"])


def is_in_personal_risk_window(user_id: str) -> dict:
    """Check if student is within 7 days of a personal exam date."""
    upcoming = get_upcoming_exams(user_id)
    for exam in upcoming:
        if exam["monitoring_elevated"]:
            return {
                "in_risk_window": True,
                "reason":         f"{exam['subject']} exam in {exam['days_remaining']} day(s)",
                "stress_window":  exam["stress_window"],
            }
    return {"in_risk_window": False}


# ─────────────────────────────────────────────────────────────────────────────
# 5. ANONYMOUS PEER PING
# ─────────────────────────────────────────────────────────────────────────────

def send_peer_ping(from_user_id: str, to_user_id: str,
                   message_type: str = "check_in") -> dict:
    """
    One student can anonymously ping another to check in.
    The recipient sees: "A friend is thinking of you 💙"
    Not who sent it. Just that someone noticed.
    """
    ping_types = {
        "check_in":   "A friend is thinking of you 💙",
        "support":    "Someone noticed you've been quiet. They're rooting for you. 🌱",
        "proud":      "A friend wanted you to know: they're proud of you. ✨",
        "you_got_it": "Exam season is hard. A friend says: you've got this. 💪",
    }
    message = ping_types.get(message_type, ping_types["check_in"])

    insert_record("peer_ping", {
        "from_user_hash": _hash_user(from_user_id),
        "to_user_id":     to_user_id,
        "message_type":   message_type,
        "message":        message,
        "ts":             datetime.utcnow().isoformat(),
        "read":           False,
    })
    return {"status": "sent", "anonymous": True}


def get_peer_pings(user_id: str) -> list:
    """Get unread pings for a user."""
    pings = query_records("peer_ping", {"to_user_id": user_id})
    unread = [p for p in pings if not p.get("read", False)]
    return [{"message": p["message"], "ts": p["ts"]} for p in unread]


# ─────────────────────────────────────────────────────────────────────────────
# PASSIVE SIGNAL FLAGGING (internal)
# ─────────────────────────────────────────────────────────────────────────────

def _flag_passive_signal(user_id: str, signal_type: str, details: dict):
    """Record a passive signal and potentially trigger behavioral monitor."""
    from services.consent_manager import has_consent
    if not has_consent(user_id, "usage_patterns"):
        return

    insert_record("passive_signal", {
        "user_id":     user_id,
        "signal_type": signal_type,
        "details":     details,
        "ts":          datetime.utcnow().isoformat(),
        "source":      "engagement_hook",
    })


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _get_focus_trend(user_id: str) -> dict:
    sessions = query_records("study_session", {"user_id": user_id})[-10:]
    if len(sessions) < 6:
        return {"declining": False, "sessions": len(sessions),
                "recent_avg": 0, "previous_avg": 0}
    recent   = [s.get("focus_score", 50) for s in sessions[-3:]]
    previous = [s.get("focus_score", 50) for s in sessions[-6:-3]]
    r_avg    = sum(recent)   / len(recent)
    p_avg    = sum(previous) / len(previous)
    return {"declining": r_avg < p_avg - 15, "sessions": len(sessions),
            "recent_avg": round(r_avg, 1), "previous_avg": round(p_avg, 1)}


def _study_streak(user_id: str) -> int:
    logs  = query_records("study_session", {"user_id": user_id})
    dates = sorted({l.get("date","") for l in logs}, reverse=True)
    if not dates:
        return 0
    streak   = 0
    check_dt = date.today()
    for d_str in dates:
        try:
            d = date.fromisoformat(d_str)
            if d == check_dt:
                streak   += 1
                check_dt -= timedelta(days=1)
            else:
                break
        except ValueError:
            break
    return streak


def _get_college_sleep_avg(college_id: str) -> float:
    cutoff = (date.today() - timedelta(days=7)).isoformat()
    logs   = [s for s in query_records("sleep_log", {"college_id": college_id})
              if s.get("date","") >= cutoff]
    if not logs:
        return 6.5  # National average default
    return round(sum(s.get("sleep_hours",6.5) for s in logs) / len(logs), 1)


def _sleep_comparison(hours: float, avg: float) -> str:
    diff = hours - avg
    if diff >= 0.5:
        return f"You slept {diff:.1f}h more than your campus average — great!"
    elif diff <= -0.5:
        return f"You slept {abs(diff):.1f}h less than your campus average."
    return "You're right at the campus average."


def _sleep_badge(hours: float) -> str:
    if hours >= 8:   return "Sleep Champion 🏆"
    if hours >= 7:   return "Well-Rested 😴"
    if hours >= 6:   return "Getting There 🌙"
    if hours >= 5:   return "Needs More Rest ⚠️"
    return "Sleep Debt Alert 🚨"


def _sleep_tip(hours: float, bedtime: int) -> str:
    if hours < 6:
        return "Less than 6h amplifies anxiety and depression significantly. Try sleeping 30 min earlier tonight."
    if bedtime >= 2:
        return "Late bedtimes disrupt your circadian rhythm. Even 11pm is better than 2am."
    return "Good sleep! Keep it consistent — same time every night matters as much as duration."


def _study_tip(focus: int, late_night: bool) -> str:
    if late_night:
        return "Studying at this hour is tough on your brain. Even a 20-min nap improves memory consolidation more than another hour of study."
    if focus < 40:
        return "Low focus today — try the 25-5 Pomodoro: 25 min on, 5 min complete break. No phone during the 25."
    if focus >= 80:
        return "Great focus session! Remember to take a proper break before the next one."
    return "Steady work. Keep it up."


def _infer_mood_from_music(genre_tags: list, track_lower: str) -> str:
    tag_str = " ".join(genre_tags).lower() + " " + track_lower
    for mood, keywords in MOOD_MUSIC_PROXY.items():
        if any(kw in tag_str for kw in keywords):
            return mood
    return "neutral"


def _get_mood_nudge(mood: str) -> str:
    nudges = {
        "sad":      "Music can reflect how we feel. If you're going through something, I'm here to listen. 💙",
        "depressed":"It's okay to sit with difficult feelings. When you're ready, I'm here.",
        "anxious":  "If things feel overwhelming, try the 4-4-4 breathing: inhale 4, hold 4, exhale 4.",
        "happy":    "Love the energy! 🎵 Keep that good mood going.",
        "focused":  "Focus mode activated. Great music choice for studying.",
    }
    return nudges.get(mood, "Whatever you're feeling right now is valid. 🎵")


def _hash_user(user_id: str) -> str:
    import hashlib
    return "anon_" + hashlib.sha256(user_id.encode()).hexdigest()[:12]
