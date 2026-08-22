"""
data/progress_store.py — Gamification + streak engine.
"""
from datetime import date, datetime
from config import settings


BADGES = {
    "first_step":        {"name": "First Step 🌱", "desc": "Opened up for the first time"},
    "streak_3":          {"name": "3-Day Streak 🔥", "desc": "Checked in 3 days in a row"},
    "streak_7":          {"name": "Mental Health Champion 🏆", "desc": "7-day streak"},
    "streak_30":         {"name": "Resilience Master 💪", "desc": "30-day streak"},
    "screened":          {"name": "Self-Aware 🧠", "desc": "Completed your first screening"},
    "logged_10":         {"name": "Self-Care Pro ✨", "desc": "10 mood check-ins"},
    "logged_50":         {"name": "Consistent Carer 🌟", "desc": "50 mood check-ins"},
    "used_resources":    {"name": "Explorer 🎵", "desc": "Used the media/resource hub"},
    "booked_counselor":  {"name": "Brave Step 🤝", "desc": "Booked a counselor session"},
    "logbook_entry":     {"name": "Journaler 📓", "desc": "Made a logbook entry"},
    "breathing_done":    {"name": "Breathwork 🌬️", "desc": "Completed a breathing exercise"},
}


def _earn_badges(streak: int, total_entries: int, events: list[str]) -> list[str]:
    earned = ["first_step"]  # Always earned after first entry

    if streak >= 3:  earned.append("streak_3")
    if streak >= 7:  earned.append("streak_7")
    if streak >= 30: earned.append("streak_30")
    if total_entries >= 10: earned.append("logged_10")
    if total_entries >= 50: earned.append("logged_50")

    for event in events:
        if event in BADGES:
            earned.append(event)

    return list(dict.fromkeys(earned))  # Deduplicate, preserve order


def update_progress(user_id: str, mood_score: int, events: list[str] = None) -> dict:
    """
    Update progress after a mood log or activity.
    Returns full progress dict with gamification.
    """
    from data.db import get_progress, save_progress

    today = date.today().isoformat()
    prev  = get_progress(user_id) or {}

    last_date = prev.get("last_mood_date")
    streak    = prev.get("streak", 0)
    total     = prev.get("total_entries", 0) + 1
    points    = prev.get("points", 0)

    # Streak logic
    if last_date == today:
        # Already logged today — don't increment streak or total again
        total  = prev.get("total_entries", 1)
        points = prev.get("points", 0)
    elif last_date:
        try:
            last_dt = date.fromisoformat(last_date)
            delta   = (date.today() - last_dt).days
            streak  = streak + 1 if delta == 1 else 1
        except ValueError:
            streak = 1
    else:
        streak = 1

    # Points
    points += settings.points_per_mood_log
    for event in (events or []):
        if event == "screened":    points += settings.points_per_screening
        elif event == "logbook":   points += settings.points_per_logbook
        elif event == "session":   points += settings.points_per_session_complete

    badges = _earn_badges(streak, total, events or [])
    badge_details = {b: BADGES[b] for b in badges if b in BADGES}

    # Mood trend (last 7 scores)
    mood_history = prev.get("mood_history", [])
    mood_history.append({"date": today, "score": mood_score})
    mood_history = mood_history[-30:]

    progress = {
        "user_id":        user_id,
        "last_mood_date": today,
        "streak":         streak,
        "total_entries":  total,
        "points":         points,
        "level":          _get_level(points),
        "badges":         badges,
        "badge_details":  badge_details,
        "mood_history":   mood_history,
    }

    save_progress(user_id, progress)
    return progress


def _get_level(points: int) -> dict:
    levels = [
        (0,   "Seedling 🌱"),
        (100, "Explorer 🌿"),
        (300, "Grower 🌳"),
        (600, "Supporter 🌟"),
        (1000,"Champion 🏆"),
        (2000,"Guardian 💎"),
    ]
    for threshold, name in reversed(levels):
        if points >= threshold:
            return {"name": name, "points": points, "next_threshold": _next_threshold(points, levels)}
    return {"name": "Seedling 🌱", "points": points, "next_threshold": 100}


def _next_threshold(points: int, levels: list) -> int:
    for threshold, _ in levels:
        if points < threshold:
            return threshold
    return 9999


def get_progress(user_id: str) -> dict:
    from data.db import get_progress as db_get
    prog = db_get(user_id)
    if not prog:
        return {
            "user_id": user_id,
            "streak": 0,
            "total_entries": 0,
            "points": 0,
            "level": _get_level(0),
            "badges": [],
            "badge_details": {},
            "mood_history": [],
            "last_mood_date": None,
        }
    return prog


# ── Story-based zone unlocks (not point scores) ───────────────────────────────
# Your idea: "You unlocked a calm zone" > "+10 points"
# Points still exist for gamification logic — zones are the story layer on top.

ZONES = [
    {"id": "first_step",     "name": "First Step 🌱",    "unlock_at": 1,   "story": "You showed up. That's everything."},
    {"id": "calm_zone",      "name": "Calm Zone 🌿",      "unlock_at": 3,   "story": "Three days in a row. Something is shifting."},
    {"id": "breath_zone",    "name": "Breath Zone 🌬️",   "unlock_at": 5,   "story": "You've practiced slowing down. That's a skill now."},
    {"id": "steady_zone",    "name": "Steady Zone ⚓",    "unlock_at": 7,   "story": "A week. Not perfect — consistent. That's what matters."},
    {"id": "explorer_zone",  "name": "Explorer Zone 🧭",  "unlock_at": 14,  "story": "Two weeks of showing up for yourself."},
    {"id": "anchor_zone",    "name": "Anchor Zone 💙",    "unlock_at": 21,  "story": "Three weeks. You're becoming someone who does this."},
    {"id": "champion_zone",  "name": "Champion Zone 🏔️", "unlock_at": 30,  "story": "Thirty days. That's not a streak — that's a habit."},
    {"id": "guardian_zone",  "name": "Guardian Zone 💎",  "unlock_at": 60,  "story": "You've been here for others as much as yourself."},
]

SELF_CARE_ACTIONS = [
    "breathing_exercise", "sleep_log", "study_session",
    "micro_challenge", "emoji_mood", "weather_mood", "peer_ping",
]
# Screening tests earn no points — they are diagnostic, not achievements.
# Only self-care actions count toward the streak.

def unlock_zone(streak: int, total_entries: int) -> dict | None:
    """Return newly unlocked zone if threshold crossed, else None."""
    # Check streak-based zones
    for zone in sorted(ZONES, key=lambda z: -z["unlock_at"]):
        if streak >= zone["unlock_at"]:
            return zone
    return None


def get_zone_progress(streak: int) -> dict:
    """Show how far to next zone unlock."""
    current_zone = None
    next_zone    = None
    for z in ZONES:
        if streak >= z["unlock_at"]:
            current_zone = z
        else:
            if next_zone is None:
                next_zone = z
    return {
        "current_zone":  current_zone,
        "next_zone":     next_zone,
        "days_to_next":  (next_zone["unlock_at"] - streak) if next_zone else 0,
        "streak":        streak,
    }
