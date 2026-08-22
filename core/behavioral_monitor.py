"""
core/behavioral_monitor.py — Behavioral Pattern Detection Engine.

Runs on every message. Detects:
  - Hyper → Calm transitions (most dangerous pre-crisis pattern)
  - Withdrawal and shutdown signals
  - Sudden silence (message length drop)
  - Bullying / ragging disclosures
  - Academic stress signals
  - Peer help requests (autism / ADHD / Down syndrome)
  - Recovery markers

Single definition of analyze_message() — no duplicates.
"""
import re
from datetime import datetime
from typing import Optional

# ── Pattern libraries ─────────────────────────────────────────────────────────

HYPER_PATTERNS = [
    r"\b(can't sleep|not sleeping|haven't slept|no sleep)\b",
    r"\b(racing thoughts|thoughts racing|mind won't stop)\b",
    r"\b(everything is amazing|feel amazing|feel invincible|on top of the world)\b",
    r"\b(don't need sleep|sleep is for|who needs sleep)\b",
    r"\b(started so many|so many ideas|doing everything)\b",
    r"\b(feel like i can do anything|unstoppable|superhuman)\b",
    r"\b(spending everything|spent so much|bought so much)\b",
    r"[A-Z]{5,}",
    r"(!{3,})",
]

SUDDEN_CALM_PATTERNS = [
    r"\b(feel at peace now|finally at peace|peace finally)\b",
    r"\b(decided|made my decision|made up my mind|it's decided)\b",
    r"\b(goodbye|good bye|farewell|take care of yourself)\b",
    r"\b(won't need|don't need this anymore|don't need to worry)\b",
    r"\b(everything sorted|sorted everything out|taken care of)\b",
    r"\b(giving away|giving my|you can have my)\b",
    r"\b(last time|final message|wanted to say)\b",
    r"\b(no more pain|pain will end|will be over soon)\b",
    r"\b(sorry for everything|sorry to everyone|forgive me)\b",
]

WITHDRAWAL_PATTERNS = [
    r"\b(don't care anymore|stopped caring|nothing matters)\b",
    r"\b(can't feel anything|feel nothing|numb|empty)\b",
    r"\b(what's the point|no point|pointless)\b",
    r"\b(nobody would notice|no one would miss|doesn't matter if i'm gone)\b",
    r"\b(stopped eating|not eating|can't eat|forgot to eat)\b",
    r"\b(haven't left|not going outside|can't go out|stuck in room)\b",
    r"\b(stopped talking|not talking to anyone|avoiding everyone)\b",
    r"\b(gave up|giving up|stopped trying)\b",
]

BULLYING_PATTERNS = [
    r"\b(being bullied|getting bullied|they bully|bullying me)\b",
    r"\b(ragging|being ragged|they rag|seniors ragging)\b",
    r"\b(cyberbullying|online harassment|trolling me|harassing me)\b",
    r"\b(making fun of me|laughing at me|humiliating|publicly shamed)\b",
    r"\b(threats|threatening me|threatened|scared of them)\b",
    r"\b(forced to do|made me do|didn't want to but they)\b",
    r"\b(excluded by everyone|ignored by everyone|no one talks to me)\b",
    r"\b(spreading rumors|false rumor|ruining my reputation)\b",
    r"\b(hit me|pushed me|physically hurt|touched without|grabbed me)\b",
    r"\b(shared my photo|private photos leaked|screenshots shared)\b",
]

ACADEMIC_STRESS_PATTERNS = [
    r"\b(failed|failing|going to fail|will fail)\b",
    r"\b(backlog|arrear|detained|rusticated)\b",
    r"\b(marks pressure|family pressure|parent pressure)\b",
    r"\b(not placed|no job offer|placement failed)\b",
    r"\b(why can't you be like|comparison with others)\b",
    r"\b(semester result|exam tomorrow|haven't studied)\b",
]

AUTISM_INDICATORS = [
    r"\b(sensory overload|too loud|too bright|overwhelming sounds)\b",
    r"\b(don't understand social|can't read people|miss social cues)\b",
    r"\b(strict routine|can't handle change|routine disrupted)\b",
    r"\b(special interest|obsessed with one thing)\b",
    r"\b(meltdown|shutdown)\b",
    r"\b(take things literally|sarcasm confusing)\b",
    r"\b(eye contact uncomfortable|avoiding eye contact)\b",
]

ADHD_INDICATORS = [
    r"\b(can't start|executive paralysis|frozen|don't know where to start)\b",
    r"\b(time blindness|lost track of time|forgot hours passed)\b",
    r"\b(rejection hurts deeply|criticism devastates)\b",
    r"\b(hyperfocus|forgot to eat because)\b",
    r"\b(forgot again|always forgetting|can't remember)\b",
    r"\b(can't stop interrupting|blurt out)\b",
]

DOWN_SYNDROME_PEER_HELP = [
    r"\b(my friend with down|classmate with disability|peer with special needs)\b",
    r"\b(how to help my friend|how do i support|what do i do for)\b",
    r"\b(friend gets confused|friend doesn't understand|communication difficulty)\b",
]

RECOVERY_MARKERS = [
    r"\b(booked|made an appointment|called the helpline|talked to someone)\b",
    r"\b(feeling slightly better|a bit better|small improvement)\b",
    r"\b(tried the breathing|did the exercise|it helped a little)\b",
    r"\b(reached out|told a friend|spoke to)\b",
]


def _scan(text: str, patterns: list) -> list:
    text_lower = text.lower()
    return [p for p in patterns if re.search(p, text_lower, re.IGNORECASE)]


# ── Single canonical analyze_message ─────────────────────────────────────────

def analyze_message(text: str) -> dict:
    """
    Analyze a single message for ALL behavioral signals.
    This is the ONLY definition — called by BehavioralTracker.ingest().
    Returns a signal dict consumed by the session and escalation chain.
    """
    hyper      = _scan(text, HYPER_PATTERNS)
    calm       = _scan(text, SUDDEN_CALM_PATTERNS)
    withdrawal = _scan(text, WITHDRAWAL_PATTERNS)
    bullying   = _scan(text, BULLYING_PATTERNS)
    academic   = _scan(text, ACADEMIC_STRESS_PATTERNS)
    autism_q   = _scan(text, AUTISM_INDICATORS)
    adhd_q     = _scan(text, ADHD_INDICATORS)
    ds_peer    = _scan(text, DOWN_SYNDROME_PEER_HELP)
    recovery   = _scan(text, RECOVERY_MARKERS)

    word_count     = len(text.split())
    bully_risk_add = len(bullying) * 2

    return {
        "ts":          datetime.utcnow().isoformat(),
        "text_length": word_count,
        "signals": {
            "hyper":                   len(hyper) > 0,
            "sudden_calm":             len(calm) > 0,
            "withdrawal":              len(withdrawal) > 0,
            "bullying":                len(bullying) > 0,
            "academic_stress":         len(academic) > 0,
            "autism_peer_help":        len(autism_q) > 0,
            "adhd_peer_help":          len(adhd_q) > 0,
            "down_syndrome_peer_help": len(ds_peer) > 0,
            "recovery":                len(recovery) > 0,
        },
        "matched": {
            "hyper":       hyper,
            "sudden_calm": calm,
            "withdrawal":  withdrawal,
            "bullying":    bullying,
        },
        "risk_score": (
            len(hyper)      * 1 +
            len(calm)       * 3 +
            len(withdrawal) * 2 +
            bully_risk_add
        ),
    }


# ── Session-level pattern tracker ─────────────────────────────────────────────

class BehavioralTracker:
    """
    Tracks signals across ALL messages in a session.
    Detects multi-message patterns like HYPER→CALM transition.
    """

    def __init__(self, user_id: str):
        self.user_id         = user_id
        self.message_signals: list = []
        self.word_counts:     list = []
        self.session_risk_level    = "low"

    def ingest(self, text: str) -> dict:
        signal = analyze_message(text)   # Single canonical call
        self.message_signals.append(signal)
        self.word_counts.append(signal["text_length"])
        self.message_signals = self.message_signals[-30:]
        self.word_counts     = self.word_counts[-30:]
        return self._assess_risk()

    def _assess_risk(self) -> dict:
        if len(self.message_signals) < 2:
            return {"risk_level": "low", "triggers": [], "escalate": False}

        triggers   = []
        risk_level = "low"
        recent     = self.message_signals[-5:]

        # ── T1: HYPER → SUDDEN CALM (most dangerous) ─────────────────────────
        hyper_recent = any(s["signals"]["hyper"]       for s in self.message_signals[-10:-3])
        calm_now     = any(s["signals"]["sudden_calm"] for s in self.message_signals[-3:])
        if hyper_recent and calm_now:
            triggers.append({
                "type":        "HYPER_TO_CALM_TRANSITION",
                "severity":    "critical",
                "description": "Hyperactive signals followed by sudden calm — high-risk pre-crisis pattern.",
            })
            risk_level = "critical"

        # ── T2: Withdrawal + calm ─────────────────────────────────────────────
        if calm_now and not hyper_recent:
            if any(s["signals"]["withdrawal"] for s in self.message_signals[-5:]):
                triggers.append({
                    "type":        "WITHDRAWAL_WITH_CALM",
                    "severity":    "high",
                    "description": "Withdrawal signals combined with sudden calm.",
                })
                risk_level = _max_level(risk_level, "high")

        # ── T3: Sudden message length drop ───────────────────────────────────
        if len(self.word_counts) >= 6:
            avg_prev = sum(self.word_counts[-6:-2]) / 4
            avg_now  = sum(self.word_counts[-2:])   / 2
            if avg_prev > 15 and avg_now < 5:
                triggers.append({
                    "type":        "SUDDEN_SILENCE",
                    "severity":    "moderate",
                    "description": f"Message length dropped from ~{avg_prev:.0f} to ~{avg_now:.0f} words.",
                })
                risk_level = _max_level(risk_level, "moderate")

        # ── T4: Sustained withdrawal ──────────────────────────────────────────
        w_count = sum(1 for s in recent if s["signals"]["withdrawal"])
        if w_count >= 3:
            triggers.append({
                "type":        "SUSTAINED_WITHDRAWAL",
                "severity":    "high",
                "description": f"Withdrawal in {w_count}/5 recent messages.",
            })
            risk_level = _max_level(risk_level, "high")

        # ── T5: Bullying detected ─────────────────────────────────────────────
        if any(s["signals"]["bullying"] for s in recent):
            triggers.append({
                "type":        "BULLYING_DETECTED",
                "severity":    "moderate",
                "description": "Student has disclosed bullying or ragging.",
            })
            risk_level = _max_level(risk_level, "moderate")

        # ── T6: Cumulative risk score ─────────────────────────────────────────
        total_risk = sum(s.get("risk_score", 0) for s in recent)
        if total_risk >= 8:
            triggers.append({
                "type":        "HIGH_CUMULATIVE_RISK",
                "severity":    "high",
                "description": f"Cumulative behavioral risk score: {total_risk}",
            })
            risk_level = _max_level(risk_level, "moderate")

        self.session_risk_level = risk_level
        return {
            "risk_level":    risk_level,
            "triggers":      triggers,
            "escalate":      risk_level in ("high", "critical"),
            "message_count": len(self.message_signals),
        }

    def get_peer_help_context(self) -> dict:
        recent = self.message_signals[-5:]
        return {
            "helping_peer_autism":        any(s["signals"]["autism_peer_help"]        for s in recent),
            "helping_peer_adhd":          any(s["signals"]["adhd_peer_help"]          for s in recent),
            "helping_peer_down_syndrome": any(s["signals"]["down_syndrome_peer_help"] for s in recent),
            "needs_peer_guidance":        any(
                s["signals"]["autism_peer_help"] or
                s["signals"]["adhd_peer_help"]   or
                s["signals"]["down_syndrome_peer_help"]
                for s in recent
            ),
        }


def _max_level(a: str, b: str) -> str:
    order = ["low", "moderate", "high", "critical"]
    return a if order.index(a) >= order.index(b) else b
