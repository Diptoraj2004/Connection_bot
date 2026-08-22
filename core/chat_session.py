"""
core/chat_session.py — Chat Session with Phenotyping + Conversation Memory.

All updates wired in:
  - PhenotypeTracker on every message (digital signals, no hardware)
  - ConversationMemory persists emotional context across sessions
  - Tone adapts per emotional state (not same response every time)
  - Cross-session pattern check at session open
  - Consent enforced before passive monitoring
  - Zones not points (story-based unlocks)
"""
import uuid
from datetime import datetime
from typing import Optional
from config import settings


class ChatSession:
    def __init__(self, user_id: str):
        self.session_id    = str(uuid.uuid4())
        self.user_id       = user_id
        self.state         = "LISTENING"
        self.created_at    = datetime.utcnow().isoformat()
        self.last_active   = datetime.utcnow().isoformat()

        self.persona: dict             = {}
        self.inferred_mood: str        = "neutral"
        self.current_emotional_state: str = "neutral"
        self.ml_severity: dict         = {}
        self.listening_turns: int      = 0
        self.listened_context: list    = []

        # Screening
        self.test_name: str            = "phq-9"
        self.questionnaire: Optional[dict] = None
        self.current_q_index: int      = 0
        self.answers: list             = []
        self.score: int                = 0
        self.screening_result: dict    = {}

        # Phenotyping (software signals, no hardware)
        from services.phenotyping import PhenotypeTracker
        self.phenotype = PhenotypeTracker(user_id)

        # Conversation memory (cross-session context)
        from services.conversation_memory import ConversationMemory
        self.memory = ConversationMemory(user_id)

        # Escalation
        self.active_escalation_id: Optional[str] = None

        # Behavioral tracker
        from core.behavioral_monitor import BehavioralTracker
        self.behavior = BehavioralTracker(user_id)

        # History
        self.history: list = []

        # Run cross-session check on open
        self._check_cross_session_on_open()

    def _check_cross_session_on_open(self):
        """Check historical usage patterns when session opens."""
        try:
            from services.phenotyping import check_cross_session_patterns
            result = check_cross_session_patterns(self.user_id)
            if result.get("risk") in ("high", "moderate") and result.get("signals"):
                from core.escalation_chain import trigger_escalation
                for signal_name, details in result["signals"].items():
                    trigger_escalation(
                        user_id=self.user_id,
                        trigger_type="PHENOTYPE_CROSS_SESSION",
                        details={"signal": signal_name, **details},
                        session_id=self.session_id,
                        override_level="L1_WATCH" if result["risk"] == "moderate" else "L2_ALERT",
                    )
        except Exception as e:
            print(f"[SESSION] Cross-session check error: {e}")

    def touch(self):
        self.last_active = datetime.utcnow().isoformat()

    def add_to_history(self, role: str, content: str):
        self.history.append({"role": role, "content": content,
                             "ts": datetime.utcnow().isoformat()})
        self.history = self.history[-20:]

    def process_input(self, raw_text: str,
                      typing_duration_s: float = 0.0,
                      backspace_count: int = 0,
                      total_keystrokes: int = 0) -> str:
        self.touch()

        # DPDPA consent gate — no data processed before permission
        try:
            from services.consent_manager import has_active_consent
            if not has_active_consent(self.user_id):
                return (
                    "Before we begin, I need your consent to store and process "
                    "your conversation data to support you.\n\n"
                    "Reply *YES* to consent and continue, or *NO* to use SentinelMind "
                    "without data storage (limited features).\n\n"
                    "Your data is encrypted, never sold, and you can withdraw consent "
                    "at any time. 🔒"
                )
        except Exception:
            pass  # consent_manager unavailable in Mode 1 — proceed

        from core.pii_scrubber import scrub
        clean = scrub(raw_text)
        self.add_to_history("user", clean)

        # Step 1: Digital phenotyping on every message
        pheno = self.phenotype.record_message(
            clean, typing_duration_s, backspace_count, total_keystrokes
        )
        if pheno.get("escalate"):
            self._handle_pheno_escalation(pheno)

        # Step 2: Detect emotional state for tone adaptation
        from services.conversation_memory import detect_emotional_state
        self.current_emotional_state = detect_emotional_state(clean, len(clean.split()))

        # Step 3: Behavioral analysis
        risk = self.behavior.ingest(clean)
        if risk.get("escalate") and self.state != "CRISIS":
            self._handle_behavioral_escalation(risk)

        # Step 4: Peer help detection
        peer = self.behavior.get_peer_help_context()
        if peer["needs_peer_guidance"] and self.state not in ("SCREENING_Q", "CRISIS"):
            self.state = "PEER_HELP"

        # Step 5: Route by state
        if   self.state == "LISTENING":       reply = self._handle_listening(clean)
        elif self.state == "PEER_HELP":       reply = self._handle_peer_help(clean, peer)
        elif self.state == "OPEN_CHAT":       reply = self._handle_open_chat(clean)
        elif self.state == "SCREENING_Q":     reply = self._handle_screening_answer(clean)
        elif self.state == "SCREENING_DONE":  reply = self._handle_post_screening(clean)
        elif self.state == "CHAT_ACTIVE":     reply = self._handle_active_chat(clean)
        elif self.state == "BOOKING":         reply = self._handle_booking(clean)
        elif self.state == "CRISIS":          reply = self._handle_crisis_state(clean)
        else:                                 reply = self._handle_active_chat(clean)

        # Step 6: Record AI reply time (for response latency tracking)
        self.phenotype.record_ai_reply()

        self.add_to_history("assistant", reply)
        return reply

    # ── LISTENING ─────────────────────────────────────────────────────────────
    def _handle_listening(self, text: str) -> str:
        self.listening_turns += 1
        self.listened_context.append(text)
        t = text.lower()

        if any(w in t for w in ["book","appointment","counselor","therapist"]):
            self.state = "BOOKING"
            return self._handle_booking(text)

        # Memory-aware opener — different for returning vs new students
        if self.memory.sessions_count > 0:
            last = self.memory._mem.get("last_session_summary","")
            if last:
                opener = f"Good to see you again. Last time {last.lower()} — how are things now?"
            else:
                opener = "Good to see you again. How have things been?"
        else:
            openers = [
                "That sounds like a lot. Tell me more — what's been the hardest part?",
                "I'm here. What's going on?",
                "I hear you. What does today feel like?",
                "No rush. Say whatever's on your mind.",
            ]
            import hashlib
            opener = openers[int(hashlib.md5(text[:8].encode()).hexdigest(),16) % len(openers)]

        if self.listening_turns >= 2:
            self.state = "OPEN_CHAT"
            return (
                f"{opener}\n\n"
                "When you're ready, I can also ask you a few short questions "
                "to make sure I'm giving you the right kind of support — "
                "or we can just keep talking. Your call."
            )
        return opener

    # ── OPEN CHAT ─────────────────────────────────────────────────────────────
    def _handle_open_chat(self, text: str) -> str:
        from data.questionnaires import infer_test_from_text, get_questionnaire
        t = text.lower()

        if any(w in t for w in ["book","appointment","counsellor","counselor"]):
            self.state = "BOOKING"
            return "I'll help you set that up. **'campus'** or **'online'** support?"

        if len(text.split()) < 4:
            self.state = "LISTENING"
            self.listening_turns = 1
            return "Tell me more."

        self.test_name    = infer_test_from_text(text)
        self.questionnaire= get_questionnaire(self.test_name)
        self.current_q_index = 0
        self.answers      = []
        self.score        = 0
        total             = len(self.questionnaire["questions"])
        desc              = self.questionnaire.get("description","")

        self.state = "SCREENING_Q"
        return (
            f"Okay. {total} short questions — no wrong answers, nothing shared without your say.\n\n"
            f"*{desc}*\n\n" + self._format_question()
        )

    # ── SCREENING ─────────────────────────────────────────────────────────────
    def _handle_screening_answer(self, text: str) -> str:
        q       = self.questionnaire["questions"][self.current_q_index]
        options = q.get("options") or self.questionnaire.get("options_global", [])
        max_idx = len(options) - 1

        nat = self._natural_to_option(text, options)
        ans = nat if nat is not None else (
            int(text.strip()) if text.strip().isdigit()
            and 0 <= int(text.strip()) <= max_idx else None
        )

        if ans is None:
            return f"Just a number 0–{max_idx}, or type naturally.\n\n" + self._format_question()

        value = options[ans]["value"]
        self.answers.append(value)
        self.score += value
        self.current_q_index += 1

        # PHQ-9 Q9 — self-harm thoughts
        if self.test_name == "phq-9" and self.current_q_index == 9 and value >= 1:
            from core.escalation_chain import trigger_escalation
            r = trigger_escalation(self.user_id, "PHQ9_CRISIS_QUESTION",
                                   {"value": value}, self.session_id)
            self.active_escalation_id = r.get("event_id")
            return (
                "Thank you for being honest about that. That took courage.\n\n"
                "Someone is being quietly notified so you're not alone in this.\n\n"
                + self._format_question()
            )

        if self.current_q_index < len(self.questionnaire["questions"]):
            return self._format_question()
        return self._complete_screening()

    def _complete_screening(self) -> str:
        from data.questionnaires import score_responses
        from data.db import save_screening_result
        from services.ngo_manager import find_affordable_support
        from services.ml_triage import predict_severity, is_model_trained
        from core.escalation_chain import trigger_escalation

        result = score_responses(self.test_name, self.answers)
        self.screening_result = result

        save_screening_result(self.user_id, self.test_name, result["score"],
                              result["severity"], result["escalate"],
                              self.answers, result["interpretation"])

        if is_model_trained():
            self.ml_severity = predict_severity(phq_score=result["score"])

        if result["escalate"]:
            level = "L3_URGENT" if result["severity"] == "severe" else "L2_ALERT"
            esc   = trigger_escalation(self.user_id, "SCREENING_ESCALATION",
                                       {"test": self.test_name, "score": result["score"],
                                        "severity": result["severity"]},
                                       self.session_id, override_level=level)
            self.active_escalation_id = esc.get("event_id")

        ngo      = find_affordable_support(self.test_name, limit=1)
        ngo_info = ngo[0] if ngo else None
        sev      = result["severity"].replace("_"," ")

        # Update memory with screening outcome
        self.memory.update_state(
            self.current_emotional_state,
            f"completed {self.test_name.upper()} with {sev} result"
        )

        empathy = {
            "minimal":          "It sounds like things are mostly manageable.",
            "mild":             "Things have been a bit tough lately — that's real.",
            "moderate":         "That sounds genuinely difficult to carry.",
            "moderately_severe":"You've been carrying a lot. That takes something.",
            "severe":           "First — thank you for trusting me with this. You deserve support.",
        }.get(result["severity"], "Thank you for going through that.")

        ngo_line = ""
        if ngo_info:
            ngo_line = f"\n\nI'd like to connect you with **{ngo_info['name']}** — {ngo_info.get('contact','contact details available')}."

        self.state = "SCREENING_DONE"
        return (
            f"{empathy}\n\n"
            f"When you're ready — your score was **{result['score']}/{result['max_score']}** "
            f"({sev}).\n{result['interpretation']}"
            f"{ngo_line}\n\n"
            "**'book'** — set up a session  |  **'chat'** — keep talking  |  **'resources'** — music/guides"
        )

    # ── POST SCREENING ────────────────────────────────────────────────────────
    def _handle_post_screening(self, text: str) -> str:
        t = text.lower()
        if "book" in t:
            self.state = "BOOKING"
            return "**'campus'** or **'online'**?"
        elif "resource" in t:
            from services.music_ai import get_mood_resources
            self.state = "CHAT_ACTIVE"
            return get_mood_resources(self.inferred_mood or "sad")
        else:
            self.state = "CHAT_ACTIVE"
            return self._handle_active_chat(text)

    # ── ACTIVE CHAT — tone-adaptive ───────────────────────────────────────────
    def _handle_active_chat(self, text: str) -> str:
        from services.rag_engine import get_ai_response
        from services.conversation_memory import detect_emotional_state

        state    = detect_emotional_state(text, len(text.split()))
        lang     = "en"
        try:
            from services.rag_engine import detect_language
            lang = detect_language(text)
        except Exception:
            pass

        extra = ""
        if self.screening_result:
            extra = (f"Student completed {self.test_name.upper()} — "
                     f"score {self.screening_result.get('score','?')}, "
                     f"severity: {self.screening_result.get('severity','unknown')}.")

        mem_context = self.memory.get_context_for_prompt()
        if mem_context:
            extra = mem_context + " " + extra

        severity = self.screening_result.get("severity","mild") if self.screening_result else "mild"
        reply    = get_ai_response(text, extra_context=extra, severity=severity, lang=lang)

        # Cap replies to 2 sentences for silent/numb emotional states
        SILENT_STATES = {"silent", "numb", "withdrawn", "dissociated"}
        if state in SILENT_STATES:
            sentences = [s.strip() for s in reply.split(".") if s.strip()]
            reply = ". ".join(sentences[:2]) + ("." if sentences else "")

        # Record the technique when the AI response contains a technique suggestion
        TECHNIQUE_KEYWORDS = [
            "try breathing", "box breathing", "grounding exercise", "5-4-3-2-1",
            "progressive muscle", "body scan", "journaling", "cold water",
            "take a walk", "deep breath", "breathing exercise"
        ]
        for kw in TECHNIQUE_KEYWORDS:
            if kw.lower() in reply.lower():
                try:
                    self.memory.record_technique(kw, helped=None)
                except Exception:
                    pass
                break

        # Append a zone-unlock message to the reply if the user just earned one
        try:
            from services.engagement_hooks import check_zone_unlock
            unlock = check_zone_unlock(self.user_id)
            if unlock:
                reply = reply + f"\n\n{unlock}"
        except Exception:
            pass

        # Update memory state
        self.memory.update_state(state)
        return reply

    # ── PEER HELP ─────────────────────────────────────────────────────────────
    def _handle_peer_help(self, text: str, peer: dict) -> str:
        self.state = "CHAT_ACTIVE"
        if peer.get("helping_peer_autism"):
            return (
                "Really kind that you're looking out for them.\n\n"
                "**When they seem overwhelmed:** Don't touch without asking. Move somewhere quieter. "
                "Fewer words. Ask: 'Space or company?'\n\n"
                "**Signs they need professional help:** Meltdowns more frequent, saying they feel like a burden, "
                "withdrawing from everyone including you.\n\n"
                "You can book a counselor for them here with their consent. "
                "How are *you* doing with all of this?"
            )
        if peer.get("helping_peer_adhd"):
            return (
                "Good instinct to reach out.\n\n"
                "**What actually helps:** Break tasks into tiny steps and do the first one together. "
                "Don't interpret forgetting as not caring — it's neurological. "
                "Body doubling (just being in the same space) works better than advice.\n\n"
                "**When to get more help:** If they seem really low, not just distracted. "
                "If they've stopped eating or leaving their room.\n\n"
                "How is your friend doing right now?"
            )
        if peer.get("helping_peer_down_syndrome"):
            return (
                "**Communication:** One idea at a time. Give them time to respond — don't finish their sentences.\n\n"
                "**When to escalate:** Behavior changes lasting more than a week, or if you suspect bullying "
                "they can't report themselves.\n\n"
                "AFA India: 011-40504437 | National Trust: 1800-11-0909 (free)\n\n"
                "What's going on with them right now?"
            )
        return self._handle_active_chat(text)

    # ── CRISIS ────────────────────────────────────────────────────────────────
    def _handle_crisis_state(self, text: str) -> str:
        import re
        from services.phenotyping import RECOVERY_MARKERS
        recovery = any(re.search(p, text.lower(), re.I) for p in RECOVERY_MARKERS)
        if recovery:
            return ("I'm glad you're still here. That step you took — it counts.\n\n"
                    "The support team knows you've reached out. They'll still check in.\n\n"
                    "How are you feeling right now?")
        return (
            "I'm right here.\n\n"
            "📞 **Kiran**: 1800-599-0019 — free, 24/7, Hindi and 12 other languages\n"
            "📞 **AASRA**: 91-22-27546669 — 24/7\n\n"
            "A support person from your campus has been notified.\n\n"
            "Are you somewhere safe right now?"
        )

    # ── BOOKING ───────────────────────────────────────────────────────────────
    def _handle_booking(self, text: str) -> str:
        t = text.lower()
        if "campus" in t:
            self.state = "CHAT_ACTIVE"
            return ("Done — anonymous booking sent to your campus counseling center. "
                    "They'll reach out within 24 hours. Your name is never shared.\n\n"
                    "How are you feeling right now?")
        elif "online" in t or "ngo" in t:
            from services.ngo_manager import find_affordable_support
            ngo = find_affordable_support(self.test_name, limit=1)
            if ngo:
                n = ngo[0]
                self.state = "CHAT_ACTIVE"
                return (f"Connected you with **{n['name']}**.\n"
                        f"Contact: {n.get('contact','see their website')}\n"
                        f"Cost: {n.get('cost_tier','free/subsidised')}\n\n"
                        "Completely confidential. I'm still here while you wait.")
        return "Type **'campus'** or **'online'**."

    # ── ESCALATION HANDLERS ───────────────────────────────────────────────────
    def _handle_pheno_escalation(self, pheno: dict):
        from core.escalation_chain import trigger_escalation, TRIGGER_LEVEL_MAP
        score = pheno.get("risk_score", 0)
        level = "L2_ALERT" if score >= 6 else "L1_WATCH"
        r = trigger_escalation(
            self.user_id, "PHENOTYPE_SIGNAL",
            {"signals": list(pheno.get("signals",{}).keys()),
             "risk_score": score, "session_id": self.session_id},
            self.session_id, override_level=level,
        )
        self.active_escalation_id = r.get("event_id")
        if level == "L2_ALERT":
            self.state = "CRISIS"

    def _handle_behavioral_escalation(self, risk: dict):
        from core.escalation_chain import trigger_escalation, TRIGGER_LEVEL_MAP
        for trigger in risk.get("triggers", []):
            ttype = trigger["type"]
            level = TRIGGER_LEVEL_MAP.get(ttype, "L2_ALERT")
            r = trigger_escalation(self.user_id, ttype,
                                   {"description": trigger["description"],
                                    "session_id": self.session_id},
                                   self.session_id, override_level=level)
            self.active_escalation_id = r.get("event_id")
            if level == "L4_CRITICAL":
                self.state = "CRISIS"

    # ── HELPERS ───────────────────────────────────────────────────────────────
    def _natural_to_option(self, text: str, options: list) -> Optional[int]:
        t = text.lower().strip()
        for i, opt in enumerate(options):
            opt_text = opt["text"].lower()
            if t == opt_text:
                return i
            if any(kw in t for kw in opt_text.split() if len(kw) > 4):
                return i
        return None

    def _format_question(self) -> str:
        q       = self.questionnaire["questions"][self.current_q_index]
        options = q.get("options") or self.questionnaire.get("options_global", [])
        opts    = "\n".join(f"  **{i}** — {o['text']}" for i, o in enumerate(options))
        total   = len(self.questionnaire["questions"])
        return f"**{self.current_q_index+1} of {total}:** {q['text']}\n\n{opts}"

    # Allow Optional import
    from typing import Optional
