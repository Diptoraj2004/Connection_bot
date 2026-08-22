"""
services/whatsapp_service.py — WhatsApp Business API Integration via Twilio.

SETUP (5 minutes):
  1. Go to console.twilio.com → Messaging → Try it out → Send a WhatsApp message
  2. Join the sandbox: WhatsApp your sandbox number with the join code shown
  3. Set Webhook URL to: {your_ngrok_url}/api/whatsapp/incoming
     - Method: POST
     - Save, then send a test message
  4. Add TWILIO_ACCOUNT_SID + TWILIO_AUTH_TOKEN to your .env

COMMON ERRORS:
  - 422 Unprocessable Entity → python-multipart not installed (pip install python-multipart)
  - 11200 HTTP retrieval failure → ngrok URL not set as webhook, or server not running
  - 11200 with timeout → LLM call >15s; we use asyncio.to_thread to prevent this

DATASET BIAS NOTE (OSMI):
  The ML triage model was trained on the OSMI Tech Survey which over-represents
  Western adult tech workers. For Indian college students aged 17-22, severity
  predictions should be treated as indicative only. The rule-based PHQ-9 scoring
  is the primary clinical decision tool.
"""

import hashlib
from config import settings


def _hash_phone(phone: str) -> str:
    """
    Hash phone number → user_id. Raw number never stored.
    wa:+919876543210 → wa_a3f7b2c1d4e5f6a7 (consistent, not reversible)
    """
    return "wa_" + hashlib.sha256(phone.encode()).hexdigest()[:16]


def parse_incoming(form_data: dict) -> dict:
    """
    Parse a Twilio WhatsApp webhook POST body.
    Twilio sends application/x-www-form-urlencoded (requires python-multipart).
    """
    body       = form_data.get("Body", "").strip()
    from_num   = form_data.get("From", "")       # e.g. "whatsapp:+919876543210"
    num_media  = int(form_data.get("NumMedia", "0") or "0")
    media_url  = form_data.get("MediaUrl0", "")
    media_type = form_data.get("MediaContentType0", "")
    msg_sid    = form_data.get("MessageSid", "")

    return {
        "user_id":    _hash_phone(from_num),
        "raw_phone":  None,               # Never stored
        "from":       from_num,
        "text":       body,               # Use "text" consistently (not "body")
        "has_media":  num_media > 0,
        "media_url":  media_url,
        "media_type": media_type,
        "msg_sid":    msg_sid,
        "channel":    "whatsapp",
    }


def build_twiml_reply(text: str) -> str:
    """
    Build a valid TwiML XML response for Twilio to deliver as WhatsApp message.
    Handles: long messages (split at 1550 chars), markdown cleanup, XML escaping.
    """
    # Convert markdown to WhatsApp formatting (WhatsApp uses * not **)
    clean = (text
             .replace("**", "*")
             .replace("__", "_")
             .replace("# ",  "")   # Remove markdown headers
             .replace("## ", "")
             .strip())

    # WhatsApp message limit is ~4096 chars, but keep well below for readability
    if len(clean) > 1550:
        clean = clean[:1500] + "\n\n[Full response available in the web app]"

    # Escape XML special characters
    clean = (clean
             .replace("&",  "&amp;")
             .replace("<",  "&lt;")
             .replace(">",  "&gt;")
             .replace('"',  "&quot;")
             .replace("'",  "&apos;"))

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Response>\n'
        f'    <Message>{clean}</Message>\n'
        '</Response>'
    )


def build_twiml_error() -> str:
    """Safe fallback TwiML when handler raises an exception."""
    return build_twiml_reply(
        "I'm having a brief connection issue. Please try again in a moment.\n\n"
        "For immediate support:\n"
        "📞 Kiran: 1800-599-0019 (free, 24/7)\n"
        "📞 AASRA: 91-22-27546669 (24/7)"
    )


async def handle_incoming_message(form_data: dict) -> str:
    """
    Full pipeline: parse → crisis check → session FSM → TwiML reply.

    Twilio timeout: 15 seconds. We use asyncio.to_thread() for all blocking
    calls so the event loop stays free. Returns valid TwiML in all cases,
    even on exceptions — Twilio needs a 200 + XML to mark delivery successful.
    """
    import asyncio

    # Always wrap in try/except — Twilio marks 422/500 as error 11200
    try:
        from core import session_manager
        from core.crisis_interceptor import check_crisis_keywords, log_crisis_event
        from data.progress_store import update_progress

        msg     = parse_incoming(form_data)
        user_id = msg["user_id"]
        text    = msg["text"]

        # Empty message — welcome reply
        if not text and not msg["has_media"]:
            return build_twiml_reply(
                "👋 Hi! I'm *SentinelMind* — a confidential mental health companion "
                "for college students.\n\n"
                "I'm here to listen, support, and connect you with help — privately and free.\n\n"
                "What would you like to do?\n\n"
                "1️⃣ *Chat* — talk about how you're feeling\n"
                "2️⃣ *Check in* — quick mood or sleep check\n"
                "3️⃣ *Resources* — helplines, counselors, NGOs\n"
                "4️⃣ *About* — what I do and how your data is protected\n\n"
                "Just reply with a number or type anything. Everything is private. 🔒🌱"
            )

        # Voice note via WhatsApp
        if msg["has_media"] and "audio" in msg.get("media_type", ""):
            try:
                reply = await _handle_voice_note(user_id, msg["media_url"])
                return build_twiml_reply(reply)
            except Exception as e:
                print(f"[WA VOICE ERROR] {e}")
                text = "[Voice message received — please type your message instead]"

        # Crisis check (deterministic — fires before LLM)
        crisis = check_crisis_keywords(text)
        if crisis["is_crisis"]:
            await asyncio.to_thread(
                log_crisis_event, user_id, "KEYWORD_WHATSAPP",
                {"matched": crisis["matched_keywords"], "channel": "whatsapp"}
            )
            return build_twiml_reply(crisis["response"])

        # Route through session FSM
        session = session_manager.get_or_create(user_id)
        reply   = await asyncio.to_thread(session.process_input, text)
        await asyncio.to_thread(update_progress, user_id, 5)

        return build_twiml_reply(reply)

    except Exception as e:
        # CRITICAL: always return valid TwiML — never let a 500 reach Twilio
        print(f"[WA HANDLER ERROR] {type(e).__name__}: {e}")
        return build_twiml_error()


async def _handle_voice_note(user_id: str, media_url: str) -> str:
    """Download a WhatsApp voice note and transcribe it via Whisper."""
    import asyncio
    import httpx
    from services.voice_service import transcribe_upload, is_whisper_available
    from core.pii_scrubber import scrub

    if not is_whisper_available():
        return "🎙️ Voice notes need Whisper installed. Please type your message instead."

    auth = (settings.twilio_account_sid, settings.twilio_auth_token)
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(media_url, auth=auth)
        resp.raise_for_status()
        audio_bytes = resp.content

    result     = await asyncio.to_thread(transcribe_upload, audio_bytes, "ogg")
    transcript = scrub(result.get("transcript", ""))
    lang       = result.get("language", "unknown")

    if not transcript:
        return "🎙️ I received your voice note but couldn't make it out. Could you type what you said?"

    from core import session_manager
    session = session_manager.get_or_create(user_id)
    reply   = await asyncio.to_thread(session.process_input, transcript)

    preview = transcript[:80] + ("..." if len(transcript) > 80 else "")
    return f"🎙️ Heard: '{preview}'\n\n{reply}"


def send_proactive_message(to_phone: str, message: str) -> bool:
    """
    Send an outbound WhatsApp message (e.g. follow-up reminders).
    to_phone format: +919876543210 (no 'whatsapp:' prefix — added here)
    """
    if not settings.twilio_account_sid or not settings.enable_whatsapp:
        print(f"[WA SEND] Simulated (WhatsApp disabled) → {to_phone[:6]}***: {message[:60]}")
        return True
    try:
        from twilio.rest import Client
        client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        client.messages.create(
            from_=settings.twilio_whatsapp_from,
            to=f"whatsapp:{to_phone}",
            body=message,
        )
        return True
    except Exception as e:
        print(f"[WA SEND ERROR] {e}")
        return False
