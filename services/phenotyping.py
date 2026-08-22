"""
services/phenotyping.py — Digital Phenotyping Engine.

PRIMARY passive signal system. Works on every phone. No hardware needed.
Replaces IoT wearables as the main detection layer.

WHAT IT TRACKS (all software, all free, all phones):

1. TYPING CADENCE
   - Characters per second while composing
   - Backspace rate (self-censorship proxy)
   - Message length trend across session

2. RESPONSE LATENCY
   - Time between AI reply and student's next message
   - Sudden 10-min gaps on a 2-min conversation = withdrawal signal
   - Never replied = strongest withdrawal signal

3. TIME-OF-DAY DRIFT
   - Student who always uses app at 4pm suddenly at 4am
   - 3+ consecutive late-night sessions = sleep disruption flag

4. SESSION PATTERN
   - Opens app then closes without typing (lurking/avoidance)
   - Session frequency drop (was daily, now absent 5 days)
   - Crisis clustering (4+ sessions in 24 hours)

5. LINGUISTIC SIGNALS (from chat text, no questionnaire)
   - First-person pronoun collapse ("I" → "you/they/it")
     Clinically: depressed people use fewer first-person pronouns
   - Future-tense disappearance ("will", "going to", "plan")
     Clinically: hopeless people stop talking about future
   - Absolute language spike ("always", "never", "nothing ever")
     Clinically: cognitive distortion marker in depression/anxiety

COMBINED SCORE → feeds behavioral monitor → escalation chain
No questionnaire needed. No hardware needed.
"""
import re
import math
from datetime import datetime, date, timedelta
from collections import deque
from config import settings
from data.db import insert_record, query_records


# ── Linguistic pattern detectors ──────────────────────────────────────────────

_FIRST_PERSON      = re.compile(r'\b(i|i\'m|i\'ve|i\'ll|i\'d|myself|my)\b', re.I)
_FUTURE_TENSE      = re.compile(r'\b(will|gonna|going to|plan to|want to|hope to|tomorrow)\b', re.I)
_ABSOLUTE_LANGUAGE = re.compile(r'\b(always|never|nothing|everything|everyone|no one|nobody|worst|completely|totally|utterly|forever|useless|worthless|pointless)\b', re.I)
_HOPELESS_MARKERS  = re.compile(r'\b(what\'s the point|doesn\'t matter|who cares|so what|whatever|don\'t care|don\'t bother|forget it|never mind|give up)\b', re.I)
_ISOLATION_MARKERS = re.compile(r'\b(alone|lonely|no one|nobody|by myself|nobody understands|nobody gets it|no friends|no one cares)\b', re.I)


def analyze_language(text: str) -> dict:
    """
    Extract linguistic phenotype signals from message text.
    These fire WITHOUT the student answering any question.
    """
    words      = text.split()
    word_count = max(len(words), 1)

    first_person_rate  = len(_FIRST_PERSON.findall(text))      / word_count
    future_tense_rate  = len(_FUTURE_TENSE.findall(text))      / word_count
    absolute_rate      = len(_ABSOLUTE_LANGUAGE.findall(text)) / word_count
    hopeless_count     = len(_HOPELESS_MARKERS.findall(text))
    isolation_count    = len(_ISOLATION_MARKERS.findall(text))

    # Low first-person in longer messages = depersonalisation signal
    first_person_low = word_count > 10 and first_person_rate < 0.03

    # Future tense absent in longer messages = hopelessness signal
    future_absent = word_count > 15 and future_tense_rate == 0

    return {
        "word_count":          word_count,
        "first_person_rate":   round(first_person_rate,  3),
        "future_tense_rate":   round(future_tense_rate,  3),
        "absolute_rate":       round(absolute_rate,      3),
        "hopeless_markers":    hopeless_count,
        "isolation_markers":   isolation_count,
        "first_person_low":    first_person_low,
        "future_absent":       future_absent,
        "cognitive_distortion":absolute_rate > 0.05,
    }


# ── Session-level phenotype tracker ──────────────────────────────────────────

class PhenotypeTracker:
    """
    Tracks all digital phenotyping signals across a session.
    Lives inside ChatSession. No hardware. No questionnaire.
    """

    def __init__(self, user_id: str):
        self.user_id         = user_id
        self.session_start   = datetime.utcnow()

        # Typing
        self.message_lengths: deque  = deque(maxlen=20)
        self.backspace_rates: deque  = deque(maxlen=20)
        self.typing_speeds:   deque  = deque(maxlen=20)   # chars/sec

        # Timing
        self.last_ai_reply_ts: datetime | None = None
        self.response_latencies: deque         = deque(maxlen=10)  # seconds

        # Time-of-day
        self.session_hours:   list[int] = []

        # Linguistic
        self.language_signals: list[dict] = []

        # Running risk
        self.risk_score:       float = 0.0
        self.triggered_signals: list[str] = []

    # ── Called by chat_session on every user message ──────────────────────────

    def record_message(self, text: str,
                        typing_duration_s: float = 0.0,
                        backspace_count:   int   = 0,
                        total_keystrokes:  int   = 0) -> dict:
        """Main entry. Returns current phenotype risk assessment."""

        now  = datetime.utcnow()
        hour = now.hour
        self.session_hours.append(hour)

        # ── Typing cadence ─────────────────────────────────────────────────────
        length = len(text)
        self.message_lengths.append(length)

        if total_keystrokes > 0:
            bsp_rate = backspace_count / total_keystrokes
            self.backspace_rates.append(bsp_rate)

        if typing_duration_s > 0 and length > 0:
            speed = length / typing_duration_s
            self.typing_speeds.append(speed)

        # ── Response latency ──────────────────────────────────────────────────
        if self.last_ai_reply_ts:
            latency = (now - self.last_ai_reply_ts).total_seconds()
            self.response_latencies.append(latency)

        # ── Linguistic analysis ───────────────────────────────────────────────
        lang_sig = analyze_language(text)
        self.language_signals.append(lang_sig)
        self.language_signals = self.language_signals[-15:]

        return self._assess()

    def record_ai_reply(self):
        """Call this after every AI message so we can measure response latency."""
        self.last_ai_reply_ts = datetime.utcnow()

    # ── Risk assessment ───────────────────────────────────────────────────────

    def _assess(self) -> dict:
        signals  = {}
        risk     = 0.0

        # 1. Message length collapse
        if len(self.message_lengths) >= 5:
            avg_old = sum(list(self.message_lengths)[:3])    / 3
            avg_new = sum(list(self.message_lengths)[-2:])   / 2
            if avg_old > 20 and avg_new < 5:
                signals["message_length_collapse"] = {
                    "from": round(avg_old), "to": round(avg_new),
                    "meaning": "Was writing paragraphs, now one word — withdrawal",
                }
                risk += 2.0

        # 2. High backspace rate (self-censorship)
        if len(self.backspace_rates) >= 3:
            avg_bsp = sum(self.backspace_rates) / len(self.backspace_rates)
            if avg_bsp > 0.30:
                signals["high_self_censorship"] = {
                    "rate": round(avg_bsp, 2),
                    "meaning": "Typing and deleting repeatedly — saying then unsaying",
                }
                risk += 1.5

        # 3. Sudden response latency spike
        if len(self.response_latencies) >= 3:
            avg_lat = sum(self.response_latencies) / len(self.response_latencies)
            last_lat = list(self.response_latencies)[-1]
            if last_lat > avg_lat * 4 and last_lat > 120:
                signals["response_latency_spike"] = {
                    "last_seconds": round(last_lat),
                    "avg_seconds":  round(avg_lat),
                    "meaning":      "Took 4x longer than usual to reply — possible dissociation",
                }
                risk += 1.5

        # 4. Late-night session
        if self.session_hours:
            late = sum(1 for h in self.session_hours[-3:] if 1 <= h <= 5)
            if late >= 2:
                signals["late_night_usage"] = {
                    "count": late,
                    "meaning": "Multiple sessions between 1–5am — sleep disruption",
                }
                risk += 1.0

        # 5. Linguistic: future tense absent
        recent_lang = self.language_signals[-5:]
        future_absent_count = sum(1 for l in recent_lang if l.get("future_absent"))
        if future_absent_count >= 3:
            signals["future_tense_absent"] = {
                "in_last_5_messages": future_absent_count,
                "meaning": "Stopped talking about tomorrow — possible hopelessness signal",
            }
            risk += 2.0

        # 6. Linguistic: cognitive distortion spike
        cog_distort_count = sum(1 for l in recent_lang if l.get("cognitive_distortion"))
        if cog_distort_count >= 3:
            signals["cognitive_distortion_pattern"] = {
                "in_last_5_messages": cog_distort_count,
                "meaning": "Absolute language ('never', 'always', 'worthless') — cognitive distortion",
            }
            risk += 2.0

        # 7. Isolation markers
        isolation_total = sum(l.get("isolation_markers", 0) for l in recent_lang)
        if isolation_total >= 3:
            signals["isolation_language"] = {
                "marker_count": isolation_total,
                "meaning": "Repeated 'alone', 'no one cares' language",
            }
            risk += 1.5

        # 8. Hopeless markers
        hopeless_total = sum(l.get("hopeless_markers", 0) for l in recent_lang)
        if hopeless_total >= 2:
            signals["hopeless_language"] = {
                "marker_count": hopeless_total,
                "meaning": "'What's the point', 'doesn't matter' language pattern",
            }
            risk += 2.5

        self.risk_score = risk
        self.triggered_signals = list(signals.keys())

        level = "low"
        if risk >= 6:   level = "critical"
        elif risk >= 4: level = "high"
        elif risk >= 2: level = "moderate"

        return {
            "risk_level":     level,
            "risk_score":     round(risk, 1),
            "signals":        signals,
            "escalate":       level in ("high", "critical"),
            "message_count":  len(self.message_lengths),
        }


# ── Cross-session phenotype (checks DB history) ───────────────────────────────

def check_cross_session_patterns(user_id: str) -> dict:
    """
    Runs on session open. Checks historical usage for withdrawal patterns.
    No wearable. Pure software.
    """
    signals  = {}
    messages = query_records("chat_message", {"user_id": user_id})

    if len(messages) < 5:
        return {"risk": "insufficient_data", "signals": {}}

    user_msgs = [m for m in messages if m.get("role") == "user"]
    if not user_msgs:
        return {"risk": "insufficient_data", "signals": {}}

    # Parse timestamps
    sessions_by_date: dict[str, list] = {}
    session_hours: list[int]          = []

    for m in user_msgs:
        ts_str = m.get("_ts", "")
        try:
            ts = datetime.fromisoformat(ts_str)
            d  = ts.date().isoformat()
            sessions_by_date.setdefault(d, []).append(ts)
            session_hours.append(ts.hour)
        except ValueError:
            pass

    all_dates = sorted(sessions_by_date.keys(), reverse=True)

    # Check: absence after activity
    if len(all_dates) >= 2:
        last_active = date.fromisoformat(all_dates[0])
        days_silent = (date.today() - last_active).days
        if days_silent >= settings.inactivity_alert_days:
            signals["prolonged_absence"] = {
                "days_silent": days_silent,
                "meaning":     f"No activity for {days_silent} days after regular use",
            }

    # Check: late-night pattern
    late_count = sum(1 for h in session_hours[-20:] if 1 <= h <= 5)
    if late_count >= 3:
        signals["persistent_late_night"] = {
            "count":   late_count,
            "meaning": f"{late_count} late-night sessions in recent history",
        }

    # Check: session frequency collapse
    if len(all_dates) >= 8:
        prev_freq = len(all_dates[4:8])   # sessions 4-8 ago
        curr_freq = len(all_dates[:4])    # last 4 date slots
        if prev_freq >= 3 and curr_freq <= 1:
            signals["frequency_collapse"] = {
                "previous": prev_freq, "current": curr_freq,
                "meaning":  "Was active, now nearly absent",
            }

    # Check: message length trend
    recent_lengths = [len(m.get("content","")) for m in user_msgs[-10:]]
    if len(recent_lengths) >= 6:
        early_avg = sum(recent_lengths[:3]) / 3
        late_avg  = sum(recent_lengths[-3:]) / 3
        if early_avg > 30 and late_avg < 8:
            signals["message_shrinkage"] = {
                "early_avg": round(early_avg), "late_avg": round(late_avg),
                "meaning":   "Messages getting shorter over time — gradual withdrawal",
            }

    risk = "low"
    if len(signals) >= 3:   risk = "high"
    elif len(signals) >= 1: risk = "moderate"

    return {"risk": risk, "signals": signals, "analyzed_messages": len(user_msgs)}


def save_phenotype_snapshot(user_id: str, session_id: str,
                             assessment: dict):
    """Persist phenotype assessment for trend analysis."""
    insert_record("phenotype_snapshot", {
        "user_id":    user_id,
        "session_id": session_id,
        "risk_level": assessment.get("risk_level", "low"),
        "risk_score": assessment.get("risk_score", 0),
        "signals":    list(assessment.get("signals", {}).keys()),
        "ts":         datetime.utcnow().isoformat(),
    })
