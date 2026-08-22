"""
services/conversation_memory.py — Emotional Context Memory.

Stores what actually happened in previous sessions so the AI
never starts cold and never repeats the same response.

TONE ADAPTATION:
  anxious   → grounding first, explain second
  silent    → gentle probe, never direct question
  resistant → indirect approach, options not instructions
  hopeless  → tiny win framing, no silver linings
  crisis    → safety only, everything else stops
  recovering→ celebrate quietly, don't rush forward
  numb      → presence without demand

NO MORE: "Try the 4-4-4 breathing exercise" every single time.
"""
from datetime import datetime
from data.db import insert_record, query_records, get_latest
from config import settings


# ── Emotional state detection from text ──────────────────────────────────────

EMOTIONAL_STATE_PATTERNS = {
    "anxious": [
        "panic", "anxious", "anxiety", "nervous", "scared", "terrified",
        "heart racing", "can't breathe", "shaking", "overwhelming", "too much",
    ],
    "silent": [
        # detected by message length < 5 words, not text content
    ],
    "resistant": [
        "don't want to", "not ready", "leave me alone", "stop asking",
        "doesn't help", "this is pointless", "waste of time", "fine", "whatever",
    ],
    "hopeless": [
        "what's the point", "doesn't matter", "nothing works", "always like this",
        "never get better", "give up", "hopeless", "pointless", "useless",
        "no future", "what's the use",
    ],
    "numb": [
        "feel nothing", "numb", "empty", "hollow", "don't feel", "can't feel",
        "don't care", "nothing", "blank",
    ],
    "crisis": [
        "suicide", "suicidal", "kill myself", "end my life", "want to die",
        "harm myself", "self harm", "not worth living", "better off dead",
    ],
    "recovering": [
        "feeling better", "a bit better", "tried it", "it helped", "getting there",
        "small improvement", "today was okay", "talked to someone", "did the breathing",
    ],
    "sad": [
        "sad", "cry", "crying", "tears", "depressed", "down", "low", "miserable",
        "unhappy", "heartbroken", "grief", "loss",
    ],
}

# ── Response tone rules per state ────────────────────────────────────────────

TONE_RULES = {
    "anxious": {
        "opener_style":      "anchor_to_now",
        "avoid":             ["here are some tips", "you should", "try this"],
        "use":               ["right now", "with me", "just this moment", "one thing"],
        "question_style":    "closed_simple",
        "max_sentences":     3,
        "technique_intro":   "Want something small that might help right now?",
        "never_say":         ["don't worry", "it will be fine", "just relax"],
    },
    "silent": {
        "opener_style":      "presence_only",
        "avoid":             ["how are you feeling?", "tell me more", "can you explain"],
        "use":               ["I'm here", "no rush", "whenever you're ready"],
        "question_style":    "none_or_yes_no",
        "max_sentences":     2,
        "technique_intro":   None,
        "never_say":         ["you need to", "you should open up", "it helps to talk"],
    },
    "resistant": {
        "opener_style":      "indirect",
        "avoid":             ["I think you should", "it would help if", "you need to"],
        "use":               ["some people find", "one option is", "you could also just"],
        "question_style":    "choice_based",
        "max_sentences":     2,
        "technique_intro":   "No pressure — you don't have to do anything right now.",
        "never_say":         ["you're resisting help", "talking about it helps", "open up"],
    },
    "hopeless": {
        "opener_style":      "validate_without_silver_lining",
        "avoid":             ["it gets better", "there's always hope", "things will improve"],
        "use":               ["that sounds real", "that makes sense given", "I hear you"],
        "question_style":    "micro_focus",
        "max_sentences":     3,
        "technique_intro":   "There's one tiny thing, if you want it.",
        "never_say":         ["look on the bright side", "things could be worse", "stay positive"],
    },
    "numb": {
        "opener_style":      "presence_not_action",
        "avoid":             ["try this exercise", "here's what helps", "do this"],
        "use":               ["I'm here", "you don't have to do anything", "just be here"],
        "question_style":    "none",
        "max_sentences":     2,
        "technique_intro":   None,
        "never_say":         ["cheer up", "snap out of it", "you'll feel better soon"],
    },
    "crisis": {
        "opener_style":      "safety_only",
        "avoid":             ["let me suggest", "here's a technique", "try breathing"],
        "use":               ["right now", "you matter", "I'm not going anywhere"],
        "question_style":    "location_safety_only",
        "max_sentences":     3,
        "technique_intro":   None,
        "never_say":         ["calm down", "it's not that bad", "think about the good things"],
    },
    "recovering": {
        "opener_style":      "quiet_celebration",
        "avoid":             ["great job!", "well done!", "proud of you!"],
        "use":               ["that took something", "that counts", "small steps are real steps"],
        "question_style":    "open_check",
        "max_sentences":     2,
        "technique_intro":   None,
        "never_say":         ["now keep it up!", "don't slip back", "make sure you"],
    },
    "sad": {
        "opener_style":      "validate_then_stay",
        "avoid":             ["cheer up", "think positive", "it could be worse"],
        "use":               ["that sounds heavy", "I hear that", "that's real"],
        "question_style":    "gentle_open",
        "max_sentences":     3,
        "technique_intro":   "Would something small help right now, or do you just want to be heard?",
        "never_say":         ["at least", "but on the bright side", "you have so much to be grateful for"],
    },
    "neutral": {
        "opener_style":      "conversational",
        "avoid":             [],
        "use":               [],
        "question_style":    "open",
        "max_sentences":     4,
        "technique_intro":   None,
        "never_say":         [],
    },
}


def detect_emotional_state(text: str, message_length: int = None) -> str:
    """
    Detect emotional state from message text.
    Returns the primary state for tone adaptation.
    """
    text_lower = text.lower()

    # Silent = very short message
    if message_length is not None and message_length < 6:
        return "silent"

    # Check in priority order (crisis must be first)
    for state, patterns in EMOTIONAL_STATE_PATTERNS.items():
        if any(p in text_lower for p in patterns):
            return state

    return "neutral"


# ── Memory store ──────────────────────────────────────────────────────────────

class ConversationMemory:
    """
    Persistent emotional context across sessions.
    The AI knows what happened before. Never starts cold.
    Never repeats itself.
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self._mem    = self._load()

    def _load(self) -> dict:
        rec = get_latest("conversation_memory", {"user_id": self.user_id})
        if rec:
            return rec
        return {
            "user_id":               self.user_id,
            "dominant_state":        "neutral",
            "state_history":         [],
            "techniques_used":       [],
            "techniques_that_helped":[],
            "last_session_summary":  "",
            "sessions_count":        0,
            "crisis_history":        False,
            "current_stressors":     [],
            "responded_to_warmth":   None,
            "last_positive_moment":  "",
        }

    def save(self):
        insert_record("conversation_memory", self._mem)

    def update_state(self, new_state: str, session_summary: str = ""):
        """Update after each session ends."""
        history = self._mem.get("state_history", [])
        history.append({
            "state": new_state,
            "ts":    datetime.utcnow().isoformat(),
        })
        self._mem["state_history"]       = history[-20:]
        self._mem["dominant_state"]      = self._get_dominant()
        self._mem["sessions_count"]      = self._mem.get("sessions_count", 0) + 1
        self._mem["last_session_summary"]= session_summary
        if new_state == "crisis":
            self._mem["crisis_history"] = True
        self.save()

    def record_technique(self, technique: str, helped: bool | None):
        used = self._mem.get("techniques_used", [])
        if technique not in used:
            used.append(technique)
        self._mem["techniques_used"] = used[-10:]

        if helped is True:
            helped_list = self._mem.get("techniques_that_helped", [])
            if technique not in helped_list:
                helped_list.append(technique)
            self._mem["techniques_that_helped"] = helped_list

        self.save()

    def get_context_for_prompt(self) -> str:
        """Build a context string for the AI system prompt."""
        parts = []
        count = self._mem.get("sessions_count", 0)
        if count > 0:
            parts.append(f"This is session {count + 1} with this student.")

        dominant = self._mem.get("dominant_state", "neutral")
        if dominant not in ("neutral",):
            parts.append(f"Their dominant recent state has been: {dominant}.")

        summary = self._mem.get("last_session_summary", "")
        if summary:
            parts.append(f"Last session: {summary}")

        helped = self._mem.get("techniques_that_helped", [])
        if helped:
            parts.append(f"Techniques that helped before: {', '.join(helped)}.")

        used = self._mem.get("techniques_used", [])
        if used:
            parts.append(f"Already tried: {', '.join(used[-3:])}. Do NOT repeat these.")

        if self._mem.get("crisis_history"):
            parts.append("Student has had a crisis event in the past. Handle with extra care.")

        stressors = self._mem.get("current_stressors", [])
        if stressors:
            parts.append(f"Known stressors: {', '.join(stressors)}.")

        return " ".join(parts) if parts else ""

    def get_tone_rules(self, current_state: str) -> dict:
        return TONE_RULES.get(current_state, TONE_RULES["neutral"])

    def _get_dominant(self) -> str:
        """Most frequent state in recent history."""
        history = self._mem.get("state_history", [])[-10:]
        if not history:
            return "neutral"
        from collections import Counter
        counts = Counter(h["state"] for h in history)
        return counts.most_common(1)[0][0]

    @property
    def dominant_state(self) -> str:
        return self._mem.get("dominant_state", "neutral")

    @property
    def sessions_count(self) -> int:
        return self._mem.get("sessions_count", 0)

    @property
    def has_crisis_history(self) -> bool:
        return self._mem.get("crisis_history", False)


# ── Tone-adaptive prompt builder ──────────────────────────────────────────────

def build_adaptive_prompt(user_input: str,
                          current_state: str,
                          memory: ConversationMemory,
                          lang: str = "en",
                          clinical_context: str = "") -> str:
    """
    Build a system prompt that adapts to the student's emotional state
    and remembers what happened before.
    NOT the same prompt every time.
    """
    tone    = memory.get_tone_rules(current_state)
    history = memory.get_context_for_prompt()

    avoid_str = ", ".join(f'"{x}"' for x in tone["avoid"][:3]) if tone["avoid"] else "nothing specific"
    use_str   = ", ".join(f'"{x}"' for x in tone["use"][:3])   if tone["use"]   else "natural language"
    never_str = ", ".join(f'"{x}"' for x in tone["never_say"][:2]) if tone["never_say"] else "nothing"

    lang_note = {
        "hi": "Respond in Hindi (Devanagari). Clinical terms can stay English.",
        "ta": "Respond in Tamil. Clinical terms can stay English.",
        "te": "Respond in Telugu. Clinical terms can stay English.",
        "bn": "Respond in Bengali. Clinical terms can stay English.",
    }.get(lang, "")

    technique_bridge = tone.get("technique_intro") or ""

    return f"""You are SentinelMind, a mental health companion for Indian college students.

CURRENT EMOTIONAL STATE: {current_state}
RESPONSE STYLE: {tone["opener_style"].replace("_", " ")}
MAX RESPONSE LENGTH: {tone["max_sentences"]} sentences

{f"SESSION HISTORY: {history}" if history else ""}
{f"CLINICAL CONTEXT: {clinical_context}" if clinical_context else ""}

TONE RULES FOR THIS STATE:
- Use language like: {use_str}
- Avoid phrases like: {avoid_str}  
- NEVER say: {never_str}
- Question style: {tone["question_style"].replace("_", " ")}
{f'- If suggesting a technique, bridge with: "{technique_bridge}"' if technique_bridge else "- Do not suggest a technique unless asked"}

CHARACTER:
- You are human-warm, not clinical-warm. Short sentences. Real reactions.
- Never start with "I understand how you feel" — it is hollow.
- Reference something specific from what they just said.
- If they did something (breathing, challenge, journaling) — celebrate quietly, not loudly.
- You have read what happened before. You are not starting over.

{lang_note}

Clinical guidelines to draw from:
{{context}}

Student says: {{user_input}}

Your response ({tone["max_sentences"]} sentences max, {tone["opener_style"].replace("_"," ")} style):"""
