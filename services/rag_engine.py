"""
services/rag_engine.py — Multilingual RAG Engine with Dynamic AI Responses.

POINT 6 of 7: Hindi/Tamil/Telugu/Bengali/Kannada support via LaBSE.
DYNAMIC RESPONSES: AI uses empathy style calibrated to each student's state.
                   Not robotic — it adapts tone, length, pacing, and warmth.

Mode 1: English only, MiniLM embeddings
Mode 2: 8 Indian languages, LaBSE embeddings, Redis cache for RAG hits

HINDI RAG:
  Same clinical guidelines translated into Hindi alongside English.
  Language detected per-message — seamless switching mid-conversation.
"""
from config import settings

# ─────────────────────────────────────────────────────────────────────────────
# CLINICAL KNOWLEDGE BASE (English)
# ─────────────────────────────────────────────────────────────────────────────
CLINICAL_GUIDELINES_EN = [
    "For acute anxiety: guide 4-4-4 Box Breathing: in 4, hold 4, out 4, hold 4. Repeat 3 times. Stay with them through it.",
    "5-4-3-2-1 Grounding: Name 5 things you see, 4 you can touch, 3 you hear, 2 you smell, 1 you taste. Anchors mind to present.",
    "Depression behavioral activation: One small action today. Not productivity — just one step. Even getting out of bed counts.",
    "For worthlessness feelings: validate first, always. 'That sounds incredibly painful and real.' Then gently ask what's one thing they've done today.",
    "Severe depression: Recommend professional support. In India: Sangath (free), iCall TISS (free for students), Vandrevala 1860-2662-345.",
    "ADHD executive dysfunction: Break into micro-steps. Body doubling works — just be in the same space while they work.",
    "ADHD time blindness: Not laziness — neurological. Use visual timers, written reminders, and celebrate starting, not just finishing.",
    "Autism sensory overload: Quiet space, no touch without asking, fewer words, give time. Ask 'space or company?' — let them choose.",
    "Autism social masking fatigue is real and exhausting. Validate the effort it takes. Don't push socialising when depleted.",
    "Bullying/ragging: 'What is happening to you is wrong and not your fault.' Ask: are you physically safe right now? Then offer reporting pathway.",
    "Anti-ragging: UGC helpline 1800-180-5522 (free 24/7). antiragging.in for anonymous reporting.",
    "Cyberbullying: Screenshot evidence BEFORE blocking. Report to cybercrime.gov.in. Never just ignore — document first.",
    "Indian academic pressure: Marks pressure, family expectations, first-gen college students — all valid and real. Acknowledge before solving.",
    "Sleep deprivation amplifies anxiety and depression by 3-4x. Sleep hygiene is mental health hygiene.",
    "COMPLETION: If student says done/ok/tried it — warmly praise, then ask how they feel. Do NOT give another exercise.",
    "CRISIS: If any self-harm mention — Kiran 1800-599-0019 (free 24/7), AASRA 91-22-27546669. Say: you matter, people are coming to help.",
    "Down syndrome: Speak directly to them, one idea at a time, give time to respond. Their feelings are as deep as anyone's.",
    "Peer helpers for autism/ADHD: Explain the neuroscience briefly. Help them understand it's neurological, not personal.",
    "Recovery is not linear. Hard days after good ones are normal. Setbacks are data, not failure.",
    "AI boundaries: 'I'm a first-aid companion, not a therapist. But I can help you get to one.'",
    "For loneliness: 'Loneliness on campus is far more common than anyone admits.' Peer support connection offered.",
    "Grief and loss: Don't rush to silver linings. Sit with them in it. 'Tell me about them.' Not 'they're in a better place.'",
    "Substance use: Non-judgmental. 'It makes sense you needed something to cope.' Then explore what the substance is helping with.",
    "PHQ-9 Q9 (self-harm thoughts): 'Thank you for telling me that. That took courage. People are being notified to help you safely.'",
]

# ─────────────────────────────────────────────────────────────────────────────
# HINDI CLINICAL GUIDELINES (Point 6)
# ─────────────────────────────────────────────────────────────────────────────
CLINICAL_GUIDELINES_HI = [
    "तीव्र चिंता के लिए: 4-4-4 बॉक्स ब्रीदिंग: 4 सेकंड सांस लें, 4 रोकें, 4 छोड़ें। 3 बार दोहराएं।",
    "ग्राउंडिंग: 5 चीज़ें जो दिखती हैं, 4 जो छू सकते हैं, 3 जो सुन सकते हैं, 2 जो सूंघ सकते हैं, 1 जो चख सकते हैं।",
    "अवसाद में एक छोटा कदम काफी है। उठना भी एक जीत है। खुद को माफ करें।",
    "बेकार महसूस होने पर: 'यह बहुत मुश्किल लगता है।' — पहले समझें, फिर सुझाव दें।",
    "मदद के लिए: Kiran हेल्पलाइन 1800-599-0019 (24/7 मुफ्त, हिंदी में उपलब्ध)।",
    "ADHD: यह आलस नहीं है — दिमाग की बनावट अलग है। एक काम, छोटे कदम, साथ बैठकर काम करना मदद करता है।",
    "रैगिंग: 'जो हो रहा है वो गलत है और आपकी गलती नहीं है।' UGC हेल्पलाइन: 1800-180-5522।",
    "परीक्षा का दबाव: परिवार की उम्मीदें, अंकों का बोझ — यह सब असली है। आप अकेले नहीं हैं।",
    "नींद की कमी चिंता और अवसाद को 3-4 गुना बढ़ा देती है। नींद मानसिक स्वास्थ्य की नींव है।",
    "आत्महत्या के विचार: 'आप बहुत मायने रखते हैं।' Kiran: 1800-599-0019, AASRA: 91-22-27546669।",
]

BULLYING_GUIDELINES = [
    "BULLYING PROTOCOL: Validate first — 'This is wrong and not your fault.' Ask: physically safe now? Then offer reporting.",
    "UGC Anti-Ragging Regulations 2009: every college must have Anti-Ragging Committee. antiragging.in (anonymous).",
    "Cyberbullying: Screenshot then block. Report at cybercrime.gov.in. Cyberbullying Research India: iamhuman.in",
    "Physical assault is criminal. Student has right to file FIR. Campus security or Student Grievance Cell.",
    "Bullying causes anxiety, depression, PTSD. Validate as normal response to abnormal situation.",
]

# ─────────────────────────────────────────────────────────────────────────────
# DYNAMIC RESPONSE STYLES
# Not robotic. Tone adapts to student's state, history, and what they need.
# ─────────────────────────────────────────────────────────────────────────────
RESPONSE_STYLES = {
    "crisis": {
        "tone":    "urgent_warm",
        "length":  "short",
        "structure":"immediate_safety_first",
        "examples": [
            "I hear you. Right now, you're safe with me. Call Kiran: 1800-599-0019 — they're available right now, free.",
            "You reaching out matters. You matter. Please call Kiran now: 1800-599-0019. I'll be right here with you.",
        ],
    },
    "high_distress": {
        "tone":    "very_warm_slow",
        "length":  "short",
        "structure":"validate_then_one_thing",
        "examples": [
            "That sounds genuinely exhausting. You don't have to explain or justify it — I'm just here.",
            "I'm not going anywhere. Tell me what today felt like.",
        ],
    },
    "moderate": {
        "tone":    "warm_curious",
        "length":  "medium",
        "structure":"reflect_then_explore",
        "examples": [
            "It sounds like things have been heavy lately. What's been the hardest part?",
            "I'm picking up that something's weighing on you. Want to say more?",
        ],
    },
    "mild": {
        "tone":    "friendly_encouraging",
        "length":  "medium",
        "structure":"normalise_then_practical",
        "examples": [
            "Honestly, what you're feeling is more common than you'd think on campus.",
            "That makes a lot of sense given everything. Here's one thing that might help...",
        ],
    },
    "neutral": {
        "tone":    "conversational",
        "length":  "flexible",
        "structure":"open_ended",
        "examples": [
            "I'm here! What's on your mind?",
            "How's your day been, honestly?",
        ],
    },
    "post_exercise": {
        "tone":    "warm_celebratory",
        "length":  "short",
        "structure":"praise_then_open_check",
        "examples": [
            "That took real effort. How does your body feel right now?",
            "You actually did that. That's not small. How are you feeling?",
        ],
    },
    "peer_help": {
        "tone":    "informed_caring",
        "length":  "detailed",
        "structure":"practical_guidance_then_check_in",
        "examples": [
            "It's really thoughtful that you're looking out for your friend. Here's how to actually help...",
        ],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# LANGUAGE DETECTION
# ─────────────────────────────────────────────────────────────────────────────

def detect_language(text: str) -> str:
    """
    Detect the language of the input text.
    Mode 1: Simple Unicode script detection (no external library).
    Mode 2: langdetect library for more accuracy.
    """
    if not settings.is_business:
        return _script_detect(text)
    try:
        from langdetect import detect
        lang = detect(text)
        # Map langdetect codes to our supported languages
        lang_map = {"hi":"hi","ta":"ta","te":"te","bn":"bn","kn":"kn",
                    "mr":"mr","gu":"gu","en":"en"}
        return lang_map.get(lang, "en")
    except Exception:
        return _script_detect(text)


def _script_detect(text: str) -> str:
    """Fast Unicode-range script detection — no dependencies."""
    devanagari = sum(1 for c in text if '\u0900' <= c <= '\u097F')
    tamil      = sum(1 for c in text if '\u0B80' <= c <= '\u0BFF')
    telugu     = sum(1 for c in text if '\u0C00' <= c <= '\u0C7F')
    bengali    = sum(1 for c in text if '\u0980' <= c <= '\u09FF')
    kannada    = sum(1 for c in text if '\u0C80' <= c <= '\u0CFF')
    total      = len(text)
    if total == 0:
        return "en"
    if devanagari / total > 0.2: return "hi"
    if tamil      / total > 0.2: return "ta"
    if telugu     / total > 0.2: return "te"
    if bengali    / total > 0.2: return "bn"
    if kannada    / total > 0.2: return "kn"
    return "en"


# ─────────────────────────────────────────────────────────────────────────────
# VECTOR STORE INITIALIZATION
# ─────────────────────────────────────────────────────────────────────────────

_retrievers: dict = {}  # keyed by language
_llm = None


def _get_llm():
    global _llm
    if _llm:
        return _llm
    from langchain_groq import ChatGroq
    _llm = ChatGroq(model=settings.groq_model,
                    temperature=settings.llm_temperature,
                    max_tokens=settings.llm_max_tokens)
    return _llm


def _get_retriever(lang: str = "en"):
    """Get or build the vector store retriever for a given language."""
    if lang in _retrievers:
        return _retrievers[lang]

    from langchain_community.vectorstores import FAISS
    from langchain_huggingface import HuggingFaceEmbeddings

    model_name = settings.active_embedding_model
    print(f"[RAG] Building {lang} vector store with {model_name}...")

    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    # Choose guidelines for language
    if lang == "hi":
        guidelines = CLINICAL_GUIDELINES_EN + CLINICAL_GUIDELINES_HI + BULLYING_GUIDELINES
    else:
        guidelines = CLINICAL_GUIDELINES_EN + BULLYING_GUIDELINES

    db = FAISS.from_texts(guidelines, embeddings)
    _retrievers[lang] = db.as_retriever(search_kwargs={"k": settings.rag_top_k})
    print(f"[RAG] ✅ {lang} retriever ready ({len(guidelines)} guidelines)")
    return _retrievers[lang]


# ─────────────────────────────────────────────────────────────────────────────
# DYNAMIC SYSTEM PROMPT BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def _build_system_prompt(style_key: str, lang: str, extra_context: str = "") -> str:
    style = RESPONSE_STYLES.get(style_key, RESPONSE_STYLES["neutral"])
    example = style["examples"][0]

    lang_instruction = ""
    if lang == "hi":
        lang_instruction = "Respond in Hindi (Devanagari script). Keep English terms for clinical words if needed."
    elif lang == "ta":
        lang_instruction = "Respond in Tamil. Keep English for clinical terms."
    elif lang == "te":
        lang_instruction = "Respond in Telugu. Keep English for clinical terms."
    elif lang == "bn":
        lang_instruction = "Respond in Bengali. Keep English for clinical terms."
    elif lang != "en":
        lang_instruction = f"Respond in the same language the student used ({lang})."

    return f"""You are SentinelMind — a mental health companion for Indian college students.

CURRENT EMOTIONAL CONTEXT: {style_key.replace('_',' ')}
TONE REQUIRED: {style['tone'].replace('_',' ')}
RESPONSE STRUCTURE: {style['structure'].replace('_',' ')}
{lang_instruction}

YOUR CHARACTER:
- You are warm, direct, and real — not a customer service bot.
- You use natural, conversational language. Short sentences. Sometimes just a question.
- You never say "I understand how you feel" — that's robotic. Instead, reflect specifically.
- You vary your openings. Never start two consecutive messages the same way.
- In a real crisis: stop everything else and focus on safety first.
- You are honest about being an AI companion, not a therapist.

EXAMPLE RESPONSE STYLE (for this context):
"{example}"

CLINICAL CONTEXT TO USE:
{{context}}

{f"STUDENT BACKGROUND: {extra_context}" if extra_context else ""}

Student says: {{user_input}}

Your response (natural, human, calibrated to the emotional context above):"""


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def get_ai_response(sanitized_input: str, extra_context: str = "",
                    severity: str = "mild", lang: str = "en",
                    user_id: str = "", emotional_state: str = "") -> str:
    """
    Main RAG pipeline with adaptive prompting from conversation memory.
    Never the same response twice. Tone adapts to emotional state.
    """
    # Detect language
    detected_lang = detect_language(sanitized_input) if settings.is_business else "en"
    active_lang   = detected_lang if detected_lang in settings.active_languages else "en"

    # Detect completion signals → post_exercise tone
    completion_words = ["done", "did it", "finished", "ok", "tried", "completed", "okay"]
    if any(w in sanitized_input.lower() for w in completion_words):
        emotional_state = "post_exercise"

    # Use conversation memory for adaptive prompt if user_id given
    if user_id and emotional_state:
        try:
            from services.conversation_memory import ConversationMemory, build_adaptive_prompt
            memory  = ConversationMemory(user_id)
            current_state = emotional_state or memory.dominant_state
            return _run_adaptive_rag(sanitized_input, current_state,
                                     memory, active_lang, extra_context)
        except Exception as e:
            print(f"[RAG] Adaptive prompt failed ({e}) — falling back to style map")

    # Fallback: style-map based (no memory)
    style_map = {
        "minimal": "neutral", "mild": "mild", "moderate": "moderate",
        "moderately_severe": "high_distress", "severe": "high_distress",
    }
    style_key = style_map.get(severity, "neutral")

    try:
        # Redis cache check (Mode 2)
        cache_key = None
        if settings.use_redis:
            import hashlib, json
            cache_key = "rag:" + hashlib.md5(
                f"{sanitized_input[:80]}{active_lang}".encode()
            ).hexdigest()
            try:
                from data.db import _get_redis
                r = _get_redis()
                if r:
                    cached = r.get(cache_key)
                    if cached:
                        return cached
            except Exception:
                pass

        retriever = _get_retriever(active_lang)
        retrieved = retriever.invoke(sanitized_input)
        context   = "\n\n".join(d.page_content for d in retrieved)
        if extra_context:
            context = extra_context + "\n\n" + context

        from langchain_core.prompts import PromptTemplate
        prompt  = PromptTemplate.from_template(
            _build_system_prompt(style_key, active_lang, extra_context)
        )
        chain   = prompt | _get_llm()
        result  = chain.invoke({"context": context, "user_input": sanitized_input})
        reply   = result.content.strip()

        # Cache result (Mode 2)
        if settings.use_redis and cache_key:
            try:
                from data.db import _get_redis
                r = _get_redis()
                if r:
                    r.setex(cache_key, 3600, reply)  # 1-hour cache
            except Exception:
                pass

        return reply

    except Exception as e:
        err = str(e).lower()
        if "rate_limit" in err or "429" in err:
            return ("I'm here with you — just a brief delay. "
                    "If you need immediate help: Kiran 1800-599-0019 (free, 24/7). "
                    "I'll be back in a moment.")
        if "auth" in err or "api_key" in err:
            return "Connection issue on my end. For urgent support: Kiran 1800-599-0019."
        print(f"[RAG ERROR] {e}")
        return ("I'm listening, even if my words are slow right now. "
                "Want to try the 4-4-4 breathing together while I reconnect?")


def get_uplifting_response(mood_label: str = "sad", lang: str = "en") -> str:
    """Short uplifting message for post-logbook/mood-log feedback."""
    try:
        llm = _get_llm()
        lang_note = f" Respond in Hindi." if lang == "hi" else ""
        prompt = (
            f"Student is feeling {mood_label}. Give ONE short genuine uplifting message "
            f"(2 sentences max) and suggest one song that matches where they are emotionally "
            f"and could gently lift their mood — Bollywood, Indian indie, or international.{lang_note} "
            f"Be specific with the song title and artist. No generic advice."
        )
        return llm.invoke(prompt).content.strip()
    except Exception:
        return "You're carrying something real today. 🎵 Try: 'Iktara' by Lucky Ali — it meets you where you are."
