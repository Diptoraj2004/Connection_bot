"""
services/silent_engagement.py — Gamified Silent Engagement for Non-Verbal Users.

THE PROBLEM: People who have given up don't want to talk.
They won't answer PHQ-9. They won't type "I'm sad."
They might, however:
  - Tap an emoji
  - Pick a color that matches their mood
  - Drag a slider
  - Choose a weather metaphor
  - React to a song recommendation
  - Complete a tiny challenge that takes 10 seconds

This module provides silent engagement pathways that:
  1. Collect clinically useful data without asking direct questions
  2. Never make the person feel interrogated or diagnosed
  3. Build tiny wins that combat helplessness
  4. Generate passive signal data for the clinical system

CLINICAL BASIS:
  - Emoji/color mood capture: validated in mHealth research (Bakker et al. 2016)
  - Behavioral activation through micro-tasks: core CBT technique
  - Self-determination theory: autonomy + competence = re-engagement
  - Gamification with meaning (not just points) maintains engagement
    in depressed populations where normal rewards feel empty
"""
from datetime import datetime, date
from data.db import insert_record, query_records
from config import settings


# ─────────────────────────────────────────────────────────────────────────────
# 1. EMOJI MOOD CAPTURE — Tap one emoji, no words needed
# ─────────────────────────────────────────────────────────────────────────────

EMOJI_MOOD_MAP = {
    # Positive
    "😊": {"mood": "happy",       "score": 8, "valence": "positive"},
    "🙂": {"mood": "okay",        "score": 6, "valence": "neutral"},
    "😌": {"mood": "calm",        "score": 7, "valence": "positive"},
    "🥳": {"mood": "excited",     "score": 9, "valence": "positive"},
    "😴": {"mood": "tired",       "score": 4, "valence": "neutral"},
    # Negative — presented without clinical framing
    "😔": {"mood": "sad",         "score": 3, "valence": "negative"},
    "😶": {"mood": "numb",        "score": 2, "valence": "negative"},
    "😤": {"mood": "angry",       "score": 3, "valence": "negative"},
    "😰": {"mood": "anxious",     "score": 3, "valence": "negative"},
    "😭": {"mood": "very_sad",    "score": 1, "valence": "negative"},
    "🥺": {"mood": "overwhelmed", "score": 2, "valence": "negative"},
    "😑": {"mood": "empty",       "score": 2, "valence": "negative"},
    "🌫️": {"mood": "foggy",       "score": 3, "valence": "negative"},  # dissociation proxy
}


def log_emoji_mood(user_id: str, emoji: str) -> dict:
    """One tap, clinically useful. No words required."""
    mapping = EMOJI_MOOD_MAP.get(emoji, {"mood": "neutral", "score": 5, "valence": "neutral"})

    insert_record("emoji_mood", {
        "user_id": user_id,
        "emoji":   emoji,
        "mood":    mapping["mood"],
        "score":   mapping["score"],
        "valence": mapping["valence"],
        "date":    date.today().isoformat(),
        "hour":    datetime.utcnow().hour,
    })

    # Also feed into mood log for progress tracking
    from data.db import save_mood_log
    save_mood_log(user_id, mapping["score"], mapping["mood"])

    # Detect sustained negative emoji pattern (3+ days of score ≤ 2)
    recent = query_records("emoji_mood", {"user_id": user_id})[-7:]
    low_count = sum(1 for r in recent if r.get("score", 5) <= 2)
    if low_count >= 3:
        _flag_silent_signal(user_id, "sustained_low_emoji_mood", {
            "consecutive_low": low_count,
            "emojis": [r.get("emoji") for r in recent[-3:]],
        })

    # Response: no clinical framing — just warmth + music
    from services.music_ai import get_resources_json
    resources = get_resources_json(mapping["mood"])

    return {
        "received":        True,
        "mood":            mapping["mood"],
        "micro_response":  _emoji_response(emoji, mapping),
        "suggested":       resources[0] if resources else None,
        "points_earned":   5,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2. WEATHER MOOD METAPHOR — "What's your weather right now?"
# ─────────────────────────────────────────────────────────────────────────────

WEATHER_MOODS = {
    "sunny":      {"mood": "happy",    "score": 8, "message": "Glad to hear it. ☀️"},
    "cloudy":     {"mood": "neutral",  "score": 5, "message": "A bit overcast — that's okay. 🌤️"},
    "rainy":      {"mood": "sad",      "score": 3, "message": "Rainy days feel heavy. I'm here. 🌧️"},
    "stormy":     {"mood": "crisis",   "score": 1, "message": "Storms are the hardest. You don't have to face this one alone. ⛈️"},
    "foggy":      {"mood": "confused", "score": 3, "message": "Foggy is okay. Sometimes we can't see far ahead. 🌫️"},
    "cold":       {"mood": "numb",     "score": 2, "message": "Cold and numb. That happens. I'm still here. ❄️"},
    "windy":      {"mood": "anxious",  "score": 3, "message": "Lots going on in your head? Let's slow it down. 💨"},
    "after_rain": {"mood": "hopeful",  "score": 6, "message": "After rain comes something. ✨"},
}


def log_weather_mood(user_id: str, weather: str) -> dict:
    """Metaphor-based mood capture. Less confronting than 'rate your mood.'"""
    mapping = WEATHER_MOODS.get(weather, WEATHER_MOODS["cloudy"])

    insert_record("weather_mood", {
        "user_id": user_id,
        "weather": weather,
        "mood":    mapping["mood"],
        "score":   mapping["score"],
        "date":    date.today().isoformat(),
    })

    from data.db import save_mood_log
    save_mood_log(user_id, mapping["score"], mapping["mood"])

    # Stormy = immediate care
    if weather == "stormy":
        _flag_silent_signal(user_id, "weather_stormy", {
            "weather": weather,
            "note":    "Student chose 'stormy' weather metaphor — possible crisis signal"
        })

    return {
        "weather":       weather,
        "message":       mapping["message"],
        "next_step":     _weather_next_step(weather),
        "points_earned": 5,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. MICRO-CHALLENGES — Tiny wins that break the helplessness loop
# ─────────────────────────────────────────────────────────────────────────────

MICRO_CHALLENGES = [
    {
        "id":          "mc_001",
        "title":       "One Breath",
        "instruction": "Take one slow breath right now. Just one. In through your nose, out through your mouth.",
        "duration_s":  10,
        "type":        "breathing",
        "points":      10,
        "why":         "Activates parasympathetic nervous system. Even one breath shifts physiological state.",
    },
    {
        "id":          "mc_002",
        "title":       "Name Three Things",
        "instruction": "Look around and name 3 things you can see right now. Just notice them.",
        "duration_s":  15,
        "type":        "grounding",
        "points":      10,
        "why":         "Grounding technique that interrupts rumination. Requires no verbal output.",
    },
    {
        "id":          "mc_003",
        "title":       "Drink Water",
        "instruction": "Go drink a glass of water. Come back when you're done.",
        "duration_s":  60,
        "type":        "self_care",
        "points":      15,
        "why":         "Dehydration worsens mood and anxiety. Self-care act builds agency.",
    },
    {
        "id":          "mc_004",
        "title":       "Stand Up",
        "instruction": "Stand up and stretch for 30 seconds. That's it. No exercise required.",
        "duration_s":  30,
        "type":        "movement",
        "points":      15,
        "why":         "Breaking physical stillness changes neurochemistry. Low bar = achievable.",
    },
    {
        "id":          "mc_005",
        "title":       "Open a Window",
        "instruction": "Open a window or step outside for 60 seconds. Fresh air and light reset the nervous system.",
        "duration_s":  60,
        "type":        "environment",
        "points":      15,
        "why":         "Natural light and air exposure directly affect serotonin and cortisol.",
    },
    {
        "id":          "mc_006",
        "title":       "Text Someone",
        "instruction": "Send one message to anyone. It can just be a meme, a song, or 'hey'. Just reach out to one human.",
        "duration_s":  120,
        "type":        "social",
        "points":      25,
        "why":         "Social connection is the strongest antidepressant known. One message is enough to activate it.",
    },
    {
        "id":          "mc_007",
        "title":       "Write One Line",
        "instruction": "Write one sentence in your logbook. It can be 'today was bad.' That's enough.",
        "duration_s":  60,
        "type":        "journaling",
        "points":      20,
        "why":         "Externalising even one feeling reduces its intensity. No pressure to elaborate.",
    },
    {
        "id":          "mc_008",
        "title":       "Put Your Phone Down",
        "instruction": "Set a 5-minute timer and do nothing. No phone. Just exist.",
        "duration_s":  300,
        "type":        "mindfulness",
        "points":      20,
        "why":         "Constant stimulation prevents emotional processing. 5 minutes of stillness resets.",
    },
]


def get_daily_challenge(user_id: str) -> dict:
    """Return today's micro-challenge, adapted to the user's current state."""
    # Check recent mood to select appropriate challenge
    recent_moods = query_records("emoji_mood", {"user_id": user_id})[-3:]
    avg_score = (sum(m.get("score", 5) for m in recent_moods) / len(recent_moods)
                 if recent_moods else 5)

    # For very low mood: easier, physical challenges (not cognitive)
    if avg_score <= 2:
        candidates = [c for c in MICRO_CHALLENGES if c["type"] in ("breathing","movement","environment")]
    elif avg_score <= 4:
        candidates = [c for c in MICRO_CHALLENGES if c["type"] in ("grounding","self_care","journaling")]
    else:
        candidates = MICRO_CHALLENGES

    # Rotate by day of year so it's consistent but varied
    from datetime import date
    day_idx = date.today().timetuple().tm_yday % len(candidates)
    challenge = candidates[day_idx]

    # Check if already completed today
    today_completions = [c for c in query_records("challenge_completion", {"user_id": user_id})
                         if c.get("date") == date.today().isoformat()]
    already_done = any(c.get("challenge_id") == challenge["id"] for c in today_completions)

    return {
        **challenge,
        "already_completed": already_done,
        "completion_count_today": len(today_completions),
        "bonus_available": len(today_completions) >= 3,
    }


def complete_challenge(user_id: str, challenge_id: str,
                       felt_better: bool = None) -> dict:
    """Mark a micro-challenge as complete. felt_better is optional signal."""
    challenge = next((c for c in MICRO_CHALLENGES if c["id"] == challenge_id), None)
    if not challenge:
        return {"error": "Challenge not found"}

    insert_record("challenge_completion", {
        "user_id":     user_id,
        "challenge_id":challenge_id,
        "challenge_type": challenge["type"],
        "felt_better": felt_better,
        "date":        date.today().isoformat(),
        "ts":          datetime.utcnow().isoformat(),
    })

    from data.progress_store import update_progress
    progress = update_progress(user_id, 6, events=["micro_challenge"])

    # felt_better = False repeatedly is a signal
    if felt_better is False:
        completions = query_records("challenge_completion", {"user_id": user_id, "felt_better": False})
        if len(completions) >= 3:
            _flag_silent_signal(user_id, "repeated_no_improvement_challenges", {
                "count": len(completions),
                "note": "Student completing challenges but not feeling better — may need escalation"
            })

    return {
        "completed":     True,
        "challenge":     challenge["title"],
        "points_earned": challenge["points"],
        "progress":      progress,
        "response":      _completion_response(challenge["type"], felt_better),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4. SILENT CHECK-IN STREAK — Just opening the app counts
# ─────────────────────────────────────────────────────────────────────────────

def log_app_open(user_id: str) -> dict:
    """
    Simply opening the app is a positive engagement signal.
    Award minimal points to build the habit. No action required.
    """
    today = date.today().isoformat()
    insert_record("app_open", {"user_id": user_id, "date": today,
                               "ts": datetime.utcnow().isoformat()})

    # Check streak
    opens = query_records("app_open", {"user_id": user_id})
    dates = sorted({o.get("date","") for o in opens}, reverse=True)
    streak = _count_streak(dates)

    milestones = {3:"🔥 3-day streak!", 7:"⭐ Week warrior!",
                  14:"💎 Two weeks strong!", 30:"🏆 30 days — that's remarkable."}
    milestone_msg = milestones.get(streak)

    return {
        "welcomed":       True,
        "streak":         streak,
        "milestone":      milestone_msg,
        "today_options": ["emoji_mood", "weather_mood", "micro_challenge", "music_log"],
        "pressure":       None,  # Explicitly no pressure message
    }


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _flag_silent_signal(user_id: str, signal_type: str, details: dict):
    from services.consent_manager import has_consent
    if not has_consent(user_id, "usage_patterns"):
        return
    insert_record("passive_signal", {
        "user_id": user_id, "signal_type": signal_type,
        "details": details, "ts": datetime.utcnow().isoformat(),
        "source": "silent_engagement",
    })
    # Check if we should flag to behavioral monitor
    high_priority = signal_type in ("weather_stormy", "sustained_low_emoji_mood",
                                     "repeated_no_improvement_challenges")
    if high_priority:
        try:
            from core.escalation_chain import trigger_escalation
            trigger_escalation(user_id, "PASSIVE_SILENT_SIGNAL",
                               {"signal": signal_type, **details},
                               override_level="L1_WATCH")
        except Exception:
            pass


def _emoji_response(emoji: str, mapping: dict) -> str:
    responses = {
        "happy":    "That's good to hear 😊",
        "okay":     "Okay is completely valid.",
        "calm":     "Calm is underrated. 🌿",
        "excited":  "Love that energy! ✨",
        "tired":    "Rest when you can. You don't always have to be on.",
        "sad":      "I see you. Today doesn't have to be better than it is.",
        "numb":     "Numb is a feeling too. I'm here.",
        "angry":    "That's real. What happened?",
        "anxious":  "Breathe with me: in 4, hold 4, out 4.",
        "very_sad": "I'm right here. You don't have to carry this alone.",
        "overwhelmed":"One thing at a time. Just one.",
        "empty":    "Empty days are the hardest. I'm still here.",
        "foggy":    "Foggy is okay. You don't have to be clear right now.",
    }
    return responses.get(mapping.get("mood","neutral"), "I hear you.")


def _weather_next_step(weather: str) -> str:
    steps = {
        "stormy":     "Would you like to talk? Or just sit here quietly for a bit?",
        "rainy":      "Sometimes rainy days just need a warm drink and patience. Is there anything you need?",
        "foggy":      "We don't need to see far. Just the next step. What's one tiny thing you could do right now?",
        "cold":       "Cold and numb pass. You've been through weather before. I'll be here.",
        "cloudy":     "Clouds move. What's one thing that brought even a small moment of okay today?",
        "sunny":      "Hold onto that. What made today feel sunnier?",
        "after_rain": "What's the small good thing that's appearing after the hard stuff?",
    }
    return steps.get(weather, "How can I help right now?")


def _completion_response(challenge_type: str, felt_better: bool = None) -> str:
    if felt_better is False:
        return ("That took real effort, even if it didn't shift things much. "
                "That happens. The effort counts. What do you need right now?")
    responses = {
        "breathing":   "One breath is enough. You did that.",
        "grounding":   "You just pulled yourself back to now. That's not nothing.",
        "self_care":   "Taking care of your body is taking care of your mind.",
        "movement":    "Your body moved. That matters.",
        "environment": "Fresh air and light are real medicine.",
        "social":      "One connection. That's the most powerful thing you just did.",
        "journaling":  "You gave that feeling somewhere to go. Well done.",
        "mindfulness": "Five minutes of stillness. More than most people manage.",
    }
    return responses.get(challenge_type, "You did that. That counts.")


def _count_streak(dates: list) -> int:
    if not dates:
        return 0
    from datetime import date, timedelta
    streak, check = 0, date.today()
    for d_str in dates:
        try:
            d = date.fromisoformat(d_str)
            if d == check:
                streak += 1
                check  -= timedelta(days=1)
            else:
                break
        except ValueError:
            break
    return streak
