# Patched: 2025-09-14 - production-ready
"""
Deterministic ChatSession state machine used by console, web and WhatsApp adapters.
Student-facing outputs never include raw numeric scores.
This module depends on data_loader and supabase_helper for question banks and storage.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime

from data_loader import get_questionnaire
import supabase_helper as sbh
from progress_store import update_progress
from config import ESCALATION_THRESHOLDS, SCORE_VISIBLE_TO_STUDENT

# Simple state constants
STATE_ONBOARD = "ONBOARD"
STATE_MOOD_PROMPT = "MOOD_PROMPT"
STATE_SELECT_SCREENING = "SELECT_SCREENING"
STATE_SCREENING_Q = "SCREENING_Q"
STATE_SCORING = "SCORING"
STATE_ESCALATION_DECISION = "ESCALATION_DECISION"
STATE_APPOINTMENT_FLOW = "APPOINTMENT_FLOW"
STATE_END = "END"

def _utcnow_iso():
    return datetime.utcnow().isoformat()

@dataclass
class ChatSession:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    channel: str = "console"
    state: str = STATE_ONBOARD
    persona: Dict[str, Any] = field(default_factory=dict)
    current_question_index: int = 0
    questionnaire: Optional[Dict[str, Any]] = None
    answers: List[Dict[str, Any]] = field(default_factory=list)
    test_name: Optional[str] = None
    last_interaction: str = field(default_factory=_utcnow_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "channel": self.channel,
            "state": self.state,
            "test_name": self.test_name,
            "current_question_index": self.current_question_index,
            "answers": self.answers,
            "last_interaction": self.last_interaction
        }

    # ----------------------
    # Flow methods
    # ----------------------
    def start_onboarding(self) -> str:
        self.state = STATE_ONBOARD
        return "Hi — what's your name? (Example reply: 'Ravi')"

    def receive_onboard(self, text: str) -> str:
        name = text.strip()
        self.persona["name"] = name
        self.state = STATE_MOOD_PROMPT
        return f"Nice to meet you, {name}. Which year are you in? (Example: '2')"

    def receive_year(self, text: str) -> str:
        self.persona["year"] = text.strip()
        self.state = STATE_MOOD_PROMPT
        return ("Thanks. Now tell me briefly how you are feeling today."
                " Example response: 'I'm feeling low today, mood 2' or just '2' (where 0=very low, 5=very good).")

    def prompt_mood(self) -> str:
        self.state = STATE_MOOD_PROMPT
        return ("On a scale of 0–5, how are you feeling right now?"
                " Example: '2' or 'I'm at 4 today'")

    def receive_mood(self, text: str) -> str:
        # Extract a numeric mood if present
        mood_value = None
        for token in text.split():
            try:
                v = int(token)
                if 0 <= v <= 5:
                    mood_value = v
                    break
            except Exception:
                pass
        if mood_value is None:
            # fallback: try to map words (simple)
            lowered = text.lower()
            if any(w in lowered for w in ["good", "well", "fine", "great"]):
                mood_value = 5
            elif any(w in lowered for w in ["ok", "okay"]):
                mood_value = 3
            else:
                mood_value = 2
        # store progress
        if self.user_id:
            update_progress(self.user_id, mood_value)
        # choose screening based on mood (deterministic mapping)
        if mood_value <= 2:
            self.test_name = "phq-9"
        elif mood_value == 3:
            self.test_name = "gad-7"
        else:
            self.test_name = "who-5"
        # load questionnaire
        try:
            self.questionnaire = get_questionnaire(self.test_name)
        except Exception:
            self.questionnaire = get_questionnaire("phq9")
            self.test_name = "phq-9"
        self.current_question_index = 0
        self.answers = []
        self.state = STATE_SCREENING_Q
        return ("📋 Let’s fill a short questionnaire to better understand how you’re feeling.\n"
                "Example answer format: reply with the number for the option, e.g., 0, 1, 2, 3.\n\n" +
                self._current_question_text())

    def _current_question_text(self) -> str:
        if not self.questionnaire or self.current_question_index >= len(self.questionnaire["questions"]):
            return "No more questions."
        q = self.questionnaire["questions"][self.current_question_index]
        options = q.get("options", [])
        opts = "\n".join([f"{i}. {opt['text']}" for i, opt in enumerate(options)])
        return f"Q{self.current_question_index+1}: {q['text']}\n{opts}"

    def receive_answer(self, text: str) -> str:
        # expect numeric option; parse best-effort
        q = self.questionnaire["questions"][self.current_question_index]
        chosen_value = None
        chosen_text = text.strip()
        # try parse single int
        try:
            tokens = [t.strip().strip(".") for t in text.split() if t.strip()]
            for t in tokens:
                if t.isdigit():
                    idx = int(t)
                    if 0 <= idx < len(q.get("options", [])):
                        chosen_value = q["options"][idx]["value"]
                        chosen_text = q["options"][idx]["text"]
                        break
        except Exception:
            chosen_value = None
        # fallback to matching option text by words
        if chosen_value is None:
            # try to match to known options by contains
            for opt in q.get("options", []):
                if opt["text"].lower() in text.lower():
                    chosen_value = opt["value"]
                    chosen_text = opt["text"]
                    break
        # final fallback: if any integer at all, use it as value
        if chosen_value is None:
            for token in text.split():
                try:
                    v = int(token)
                    chosen_value = v
                    break
                except Exception:
                    continue
        # Save answer (numeric_value may still be None)
        ans = {
            "question_id": q["id"],
            "question_text": q["text"],
            "answer_text": chosen_text,
            "numeric_value": chosen_value
        }
        self.answers.append(ans)
        # Persist via sbh.log_response (non-blocking in production — here it's local)
        try:
            sbh.log_response(user_id=self.user_id, session_id=self.session_id, channel=self.channel,
                             test_name=self.test_name, question_id=q["id"], question_text=q["text"],
                             answer_text=chosen_text, numeric_value=chosen_value, modality="text")
        except Exception:
            pass
        # move next
        self.current_question_index += 1
        if self.current_question_index >= len(self.questionnaire["questions"]):
            self.state = STATE_SCORING
            return self._process_scoring()
        else:
            return self._current_question_text()

    def _score_answers(self) -> int:
        total = 0
        for a in self.answers:
            v = a.get("numeric_value")
            if isinstance(v, int):
                total += v
        return total

    def _process_scoring(self) -> str:
        raw_score = self._score_answers()
        # store numeric score for counselors / ML
        sbh.record_score(user_id=self.user_id, session_id=self.session_id, test_name=self.test_name, raw_score=raw_score, interpreted="", details={"answers_count": len(self.answers)})
        # decide escalation
        threshold = ESCALATION_THRESHOLDS.get(self.test_name.upper(), None)
        # map phq9 id style
        if threshold is None:
            # try mapping common names
            threshold = ESCALATION_THRESHOLDS.get(self.test_name.replace("-", "_").upper(), None)
        # Determine level
        level = "info"
        if threshold is not None and raw_score >= threshold:
            level = "critical"
        # Create alert for counselors if needed
        if level in ("warning", "critical"):
            sbh.create_alert(user_id=self.user_id, session_id=self.session_id, test_name=self.test_name, score=raw_score, level=level, details={"answers": self.answers}, notify_methods=None)
        # Student-facing message: supportive only (do not share numeric score)
        supportive = ("Thanks — I've noted how you're feeling. I can't show raw scores here, but if you'd like "
                      "I can offer a short breathing exercise, self-help tips, or help to book a session with a counsellor. "
                      "Would you like any of those now? (Example: 'breathing', 'tips', 'book')")
        self.state = STATE_APPOINTMENT_FLOW
        return supportive

    def handle_post_screening_choice(self, text: str) -> str:
        t = text.lower()
        if "breath" in t:
            return _breathing_text()
        if "tip" in t:
            return _self_care_tips()
        if "book" in t or "appointment" in t:
            return "Okay — I can help you book an appointment. Please tell me your preferred date/time (example: 'tomorrow 3pm')."
        return "I can help with breathing, self-care tips, or booking a session. Which would you prefer?"

def _breathing_text() -> str:
    return ("Let's try a simple 4-4-4 breathing exercise:\n"
            "Inhale slowly for 4 seconds — hold 4 seconds — exhale for 4 seconds. Repeat this 4 times. "
            "Would you like to do that now?")

def _self_care_tips() -> str:
    return ("Here are some quick self-care tips:\n"
            "• Try 5 minutes of deep breathing\n"
            "• Drink some water and take a short walk\n"
            "• Do a grounding exercise: name 3 things you can see, 2 you can touch, 1 you can hear\n"
            "If you'd like professional support, I can help connect you to a counsellor.")
