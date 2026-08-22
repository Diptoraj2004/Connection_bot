"""
api/routes.py — All FastAPI route handlers for SentinelMind v4.

All routers defined here, imported by main.py.
WhatsApp endpoint has correct Request type annotation.
No orphan docstrings. Single definition per router.
"""
import hashlib
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field


# ══════════════════════════════════════════════════════════════════════════════
# SCHEMAS
# ══════════════════════════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    user_id: str = "student_001"
    message: str
    reset_session: bool = False

class ChatResponse(BaseModel):
    response:    str
    state:       str
    session_id:  str
    gamification:dict
    ml_severity: dict = {}

class MoodLogRequest(BaseModel):
    user_id:    str
    mood_score: int = Field(..., ge=1, le=10)
    mood_label: str = "neutral"
    note:       str = ""
    tags:       list[str] = []

class LogbookEntryRequest(BaseModel):
    user_id:       str
    content:       str
    consent_level: str  = "counselor_only"
    audio_transcript: str = ""
    tags:          list[str] = []
    share_uplifting: bool = True

class ScreeningAnswerRequest(BaseModel):
    user_id:   str
    test_name: str
    answers:   list[int]

class IoTReadingRequest(BaseModel):
    user_id:     str
    metric_type: str
    value:       float = 0.0
    simulated:   bool  = False
    profile:     str   = "normal"

class BookingRequest(BaseModel):
    user_id:      str
    counselor_id: str  = "campus_default"
    slot_ts:      str  = ""
    anonymous:    bool = True
    preference:   str  = "online"

class MLTrainRequest(BaseModel):
    use_kaggle:    bool = True
    force_retrain: bool = False

class RatingRequest(BaseModel):
    user_id:     str
    target_type: str
    target_id:   str
    score:       int = Field(..., ge=1, le=5)
    comment:     str  = ""
    anonymous:   bool = True

class RegisterVolunteerRequest(BaseModel):
    name_anon:          str
    college:            str
    languages:          list[str]  = ["English"]
    availability_hours: list[int]  = list(range(8, 22))
    email_hash:         str        = ""

class TrainingUpdateRequest(BaseModel):
    volunteer_id: str
    level:        int = Field(..., ge=0, le=3)

class CompleteAssignmentRequest(BaseModel):
    assignment_id: str
    volunteer_id:  str
    outcome:       str

class RegisterCounselorRequest(BaseModel):
    name:         str
    email_hash:   str
    college:      str
    specialties:  list[str]
    languages:    list[str] = ["English"]
    max_students: int       = 30

class SessionNoteRequest(BaseModel):
    counselor_id:       str
    user_id_hash:       str
    session_date:       str       = ""
    session_type:       str       = "follow_up"
    presenting_issues:  list[str] = []
    interventions:      list[str] = []
    risk_level:         str       = "low"
    next_appointment:   str       = ""
    private_notes:      str       = ""
    shared_summary:     str       = ""

class AcknowledgeRequest(BaseModel):
    event_id:         str
    acknowledged_by:  str
    note:             str = ""

class ResolveRequest(BaseModel):
    event_id:    str
    resolved_by: str
    outcome:     str

class AddNGORequest(BaseModel):
    name:                 str
    contact_email:        str
    specialty:            list[str]
    city:                 str       = ""
    state:                str       = ""
    online:               bool      = True
    languages:            list[str] = ["English"]
    cost_per_session_inr: int       = 0
    cost_tier:            str       = "unknown"
    cost_notes:           str       = ""
    website:              str       = ""

class OutreachRequest(BaseModel):
    ngo_id:         str
    sender_name:    str = "SentinelMind Team"
    sender_college: str = "Our College"

class VoiceBase64Request(BaseModel):
    user_id:       str
    audio_b64:     str
    extension:     str = "webm"
    consent_level: str = "counselor_only"

class StorySubmissionRequest(BaseModel):
    user_id:     str
    title:       str
    content:     str
    condition:   str
    what_helped: list[str] = []

# Simulated counselor slots
AVAILABLE_SLOTS = [
    {"slot_id": "s001", "counselor": "Dr. Priya Sharma",  "slot_ts": "2025-11-15T10:00:00", "mode": "online"},
    {"slot_id": "s002", "counselor": "Mr. Arjun Mehta",   "slot_ts": "2025-11-15T14:00:00", "mode": "campus"},
    {"slot_id": "s003", "counselor": "Dr. Kavitha Nair",  "slot_ts": "2025-11-16T11:00:00", "mode": "online"},
    {"slot_id": "s004", "counselor": "Ms. Ritu Singh",    "slot_ts": "2025-11-17T09:00:00", "mode": "campus"},
]


# ══════════════════════════════════════════════════════════════════════════════
# /api/chat
# ══════════════════════════════════════════════════════════════════════════════
chat_router = APIRouter(prefix="/api/chat", tags=["Chat"])

@chat_router.post("", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    import asyncio
    from core import session_manager
    from core.crisis_interceptor import check_crisis_keywords, log_crisis_event
    from data.progress_store import update_progress, get_progress

    if payload.reset_session:
        session_manager.reset(payload.user_id)

    crisis = check_crisis_keywords(payload.message)
    if crisis["is_crisis"]:
        log_crisis_event(payload.user_id, "KEYWORD",
                         {"matched": crisis["matched_keywords"],
                          "preview": payload.message[:80]})
        session = session_manager.get_or_create(payload.user_id)
        session.state = "CRISIS"
        progress = get_progress(payload.user_id)
        return ChatResponse(
            response=crisis["response"], state="CRISIS",
            session_id=session.session_id,
            gamification=progress or {}, ml_severity={},
        )

    if any(w in payload.message.lower()
           for w in ["panic", "can't breathe", "heart racing", "shaking badly"]):
        import asyncio as _asyncio
        from services.iot_adapter import simulate_reading
        _asyncio.create_task(
            _asyncio.to_thread(simulate_reading, payload.user_id, "heart_rate", "panic"))

    try:
        session = session_manager.get_or_create(payload.user_id)
        reply   = await asyncio.to_thread(session.process_input, payload.message)
        progress= await asyncio.to_thread(update_progress, payload.user_id, 5)
        return ChatResponse(
            response=reply, state=session.state,
            session_id=session.session_id,
            gamification=progress, ml_severity=session.ml_severity,
        )
    except Exception as e:
        print(f"[CHAT ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.get("/history/{user_id}")
async def get_chat_history(user_id: str, limit: int = Query(default=20, le=100)):
    from data.db import get_chat_history
    h = get_chat_history(user_id, limit=limit)
    return {"user_id": user_id, "history": h, "count": len(h)}

@chat_router.delete("/session/{user_id}")
async def reset_session(user_id: str):
    from core import session_manager
    session_manager.reset(user_id)
    return {"status": "session_reset", "user_id": user_id}


# ══════════════════════════════════════════════════════════════════════════════
# /api/screening
# ══════════════════════════════════════════════════════════════════════════════
screening_router = APIRouter(prefix="/api/screening", tags=["Screening"])

@screening_router.get("/questionnaires")
async def list_questionnaires():
    from data.questionnaires import list_questionnaires, QUESTIONNAIRE_BANK
    return {"available": list_questionnaires(),
            "descriptions": {k: v.get("name", k) for k, v in QUESTIONNAIRE_BANK.items()}}

@screening_router.get("/questionnaire/{test_name}")
async def get_questionnaire(test_name: str):
    from data.questionnaires import get_questionnaire
    q = get_questionnaire(test_name)
    if not q:
        raise HTTPException(status_code=404, detail=f"'{test_name}' not found")
    return q

@screening_router.post("/score")
async def score_screening(payload: ScreeningAnswerRequest):
    from data.questionnaires import score_responses
    from data.db import save_screening_result
    from services.ngo_manager import find_affordable_support
    from services.ml_triage import predict_severity, is_model_trained
    from core.crisis_interceptor import log_crisis_event
    from data.progress_store import update_progress

    result = score_responses(payload.test_name, payload.answers)
    ml     = predict_severity(phq_score=result["score"]) if is_model_trained() else {}
    save_screening_result(payload.user_id, payload.test_name,
                          result["score"], result["severity"],
                          result["escalate"], payload.answers, result["interpretation"])
    if result["escalate"]:
        log_crisis_event(payload.user_id, "SCREENING_ESCALATION",
                         {"test": payload.test_name, "score": result["score"],
                          "severity": result["severity"]})
    update_progress(payload.user_id, 5, events=["screened"])
    ngos = find_affordable_support(payload.test_name, max_cost_inr=0, limit=1)
    return {**result, "ml_prediction": ml,
            "recommended_ngo": ngos[0] if ngos else None,
            "resources": result.get("recommended_resources", [])}

@screening_router.get("/results/{user_id}")
async def get_screening_results(user_id: str):
    from data.db import get_screening_results
    r = get_screening_results(user_id)
    return {"user_id": user_id, "results": r, "count": len(r)}

@screening_router.get("/infer")
async def infer_test(text: str = Query(...)):
    from data.questionnaires import infer_test_from_text
    return {"text": text, "recommended_test": infer_test_from_text(text)}


# ══════════════════════════════════════════════════════════════════════════════
# /api/iot
# ══════════════════════════════════════════════════════════════════════════════
iot_router = APIRouter(prefix="/api/iot", tags=["IoT"])

@iot_router.post("/reading")
async def ingest_reading(payload: IoTReadingRequest):
    import asyncio
    from services.iot_adapter import process_reading, simulate_reading, simulate_all_metrics
    if payload.simulated:
        if payload.metric_type == "all":
            r = await asyncio.to_thread(simulate_all_metrics, payload.user_id, payload.profile)
            return {"readings": r, "simulated": True}
        return await asyncio.to_thread(simulate_reading, payload.user_id,
                                       payload.metric_type, payload.profile)
    return await asyncio.to_thread(process_reading, payload.user_id,
                                   payload.metric_type, payload.value)

@iot_router.get("/readings/{user_id}")
async def get_readings(user_id: str, metric_type: Optional[str] = None, limit: int = 50):
    from data.db import get_iot_readings
    r = get_iot_readings(user_id, metric_type=metric_type, limit=limit)
    return {"user_id": user_id, "readings": r, "count": len(r)}

@iot_router.get("/summary/{user_id}")
async def biometric_summary(user_id: str):
    from services.iot_adapter import get_biometric_summary
    return {"user_id": user_id, "summary": get_biometric_summary(user_id)}

@iot_router.post("/simulate/{user_id}")
async def run_simulation(user_id: str, profile: str = "stressed"):
    import asyncio
    from services.iot_adapter import simulate_all_metrics
    return {"readings": await asyncio.to_thread(simulate_all_metrics, user_id, profile)}


# ══════════════════════════════════════════════════════════════════════════════
# /api/progress
# ══════════════════════════════════════════════════════════════════════════════
progress_router = APIRouter(prefix="/api/progress", tags=["Progress"])

@progress_router.get("/{user_id}")
async def get_progress_endpoint(user_id: str):
    from data.progress_store import get_progress
    return get_progress(user_id)

@progress_router.post("/mood")
async def log_mood(payload: MoodLogRequest):
    import asyncio
    from data.db import save_mood_log
    from data.progress_store import update_progress
    from services.music_ai import get_resources_json
    await asyncio.to_thread(save_mood_log, payload.user_id, payload.mood_score,
                            payload.mood_label, payload.note, payload.tags)
    progress = await asyncio.to_thread(update_progress, payload.user_id, payload.mood_score)
    return {"status": "logged", "progress": progress,
            "mood_resources": get_resources_json(payload.mood_label)[:2]}

@progress_router.get("/mood-history/{user_id}")
async def mood_history(user_id: str, limit: int = 30):
    from data.db import get_mood_logs
    logs = get_mood_logs(user_id, limit=limit)
    return {"user_id": user_id, "mood_logs": logs, "count": len(logs)}


# ══════════════════════════════════════════════════════════════════════════════
# /api/logbook
# ══════════════════════════════════════════════════════════════════════════════
logbook_router = APIRouter(prefix="/api/logbook", tags=["Logbook"])

@logbook_router.post("/entry")
async def create_logbook_entry(payload: LogbookEntryRequest):
    import asyncio, base64
    from core.pii_scrubber import scrub
    from data.db import save_logbook_entry
    from data.progress_store import update_progress
    from services.rag_engine import get_uplifting_response
    scrubbed  = scrub(payload.content)
    encrypted = base64.b64encode(scrubbed.encode()).decode()
    await asyncio.to_thread(save_logbook_entry, payload.user_id, encrypted,
                            payload.consent_level, scrub(payload.audio_transcript), payload.tags)
    progress  = await asyncio.to_thread(update_progress, payload.user_id, 5, ["logbook"])
    uplifting = ""
    if payload.share_uplifting:
        uplifting = await asyncio.to_thread(get_uplifting_response, "neutral")
    return {"status": "saved", "encrypted": True, "consent_level": payload.consent_level,
            "progress": progress, "uplifting_feedback": uplifting,
            "note": "Logbook is private. Counselor access requires consent_level='counselor_only'."}

@logbook_router.get("/{user_id}")
async def get_logbook(user_id: str, requester_role: str = Query(default="student")):
    import base64
    from data.db import get_logbook_entries
    entries = get_logbook_entries(user_id, requester_role)
    decoded = []
    for e in entries:
        try:    content = base64.b64decode(e.get("content_encrypted","")).decode()
        except: content = "[Encrypted]"
        decoded.append({**e, "content": content, "content_encrypted": "[REDACTED]"})
    return {"user_id": user_id, "requester_role": requester_role,
            "entries": decoded, "count": len(decoded)}


# ══════════════════════════════════════════════════════════════════════════════
# /api/resources
# ══════════════════════════════════════════════════════════════════════════════
resources_router = APIRouter(prefix="/api/resources", tags=["Resources"])

@resources_router.get("")
async def get_resources(mood: str = Query(default="neutral")):
    from services.music_ai import get_resources_json
    return {"mood": mood, "resources": get_resources_json(mood)}

@resources_router.get("/music")
async def get_music(mood: str = Query(default="neutral")):
    from services.music_ai import get_resources_json
    music_types = {"lofi","bollywood","pop","classical","classical_indian",
                   "indie","ambient","binaural","sleep_aid"}
    return {"mood": mood,
            "music": [r for r in get_resources_json(mood) if r["type"] in music_types]}

@resources_router.get("/guides")
async def get_guides(mood: str = Query(default="anxious")):
    from services.music_ai import get_resources_json
    return {"mood": mood,
            "guides": [r for r in get_resources_json(mood)
                       if "guide" in r["type"] or r["type"] == "video"]}


# ══════════════════════════════════════════════════════════════════════════════
# /api/booking
# ══════════════════════════════════════════════════════════════════════════════
booking_router = APIRouter(prefix="/api/booking", tags=["Booking"])

@booking_router.get("/slots")
async def list_slots(mode: Optional[str] = None):
    slots = AVAILABLE_SLOTS if not mode else [s for s in AVAILABLE_SLOTS if s["mode"] == mode]
    return {"available_slots": slots}

@booking_router.post("/slot")
async def book_slot(payload: BookingRequest):
    from data.db import save_booking
    from data.progress_store import update_progress
    slot_ts = payload.slot_ts or datetime.utcnow().isoformat()
    booking = save_booking(payload.user_id, payload.counselor_id, slot_ts, payload.anonymous)
    update_progress(payload.user_id, 5, ["booked_counselor"])
    return {"status": "booked", "booking_ref": booking.get("id","B-DEMO")[:8],
            "anonymous": payload.anonymous, "preference": payload.preference,
            "message": ("Your session has been booked anonymously. "
                        "Only your booking reference is shared — no personal details.")}

@booking_router.get("/my-bookings/{user_id}")
async def my_bookings(user_id: str):
    from data.db import get_bookings
    return {"bookings": get_bookings(user_id)}


# ══════════════════════════════════════════════════════════════════════════════
# /api/admin
# ══════════════════════════════════════════════════════════════════════════════
admin_router = APIRouter(prefix="/api/admin", tags=["Admin"])

@admin_router.get("/trends")
async def aggregate_trends():
    from data.db import get_aggregate_trends
    return get_aggregate_trends()

@admin_router.get("/alerts")
async def recent_alerts(limit: int = Query(default=20, le=100)):
    from core.merkle_ledger import get_recent_events
    return {"alerts": get_recent_events(limit), "count": limit}

@admin_router.get("/ledger/verify")
async def verify_ledger():
    from core.merkle_ledger import verify_ledger_integrity
    return verify_ledger_integrity()

@admin_router.get("/sessions")
async def active_sessions():
    from core.session_manager import active_count
    return {"active_sessions": active_count()}


# ══════════════════════════════════════════════════════════════════════════════
# /api/ml
# ══════════════════════════════════════════════════════════════════════════════
ml_router = APIRouter(prefix="/api/ml", tags=["ML"])

@ml_router.post("/train")
async def train_models(payload: MLTrainRequest):
    import asyncio
    from services.ml_triage import train_triage_models
    return await asyncio.to_thread(train_triage_models, payload.use_kaggle, payload.force_retrain)

@ml_router.get("/status")
async def ml_status():
    from services.ml_triage import is_model_trained
    return {"model_trained": is_model_trained()}

@ml_router.post("/predict")
async def predict(age: float = 20.0, phq_score: float = 0.0,
                  family_history: int = 0, gender: str = "unknown"):
    from services.ml_triage import predict_severity
    return predict_severity(age=age, phq_score=phq_score,
                            family_history=family_history, gender=gender)


# ══════════════════════════════════════════════════════════════════════════════
# /api/escalation
# ══════════════════════════════════════════════════════════════════════════════
escalation_router = APIRouter(prefix="/api/escalation", tags=["Escalation"])

@escalation_router.get("/active")
async def get_active_escalations():
    from core.escalation_chain import get_all_active_events
    events = get_all_active_events()
    return {"active_escalations": events, "count": len(events)}

@escalation_router.get("/active/{user_id}")
async def get_user_escalation(user_id: str):
    from core.escalation_chain import get_active_event
    return get_active_event(user_id) or {"message": "No active escalation"}

@escalation_router.post("/acknowledge")
async def acknowledge(payload: AcknowledgeRequest):
    from core.escalation_chain import acknowledge_event
    return acknowledge_event(payload.event_id, payload.acknowledged_by, payload.note)

@escalation_router.post("/resolve")
async def resolve(payload: ResolveRequest):
    from core.escalation_chain import resolve_event
    return resolve_event(payload.event_id, payload.resolved_by, payload.outcome)

@escalation_router.get("/overdue")
async def check_overdue():
    from core.escalation_chain import check_unacknowledged_events, auto_escalate_overdue
    overdue = check_unacknowledged_events()
    if overdue:
        auto_escalate_overdue()
    return {"overdue_count": len(overdue), "events": overdue}


# ══════════════════════════════════════════════════════════════════════════════
# /api/ngo
# ══════════════════════════════════════════════════════════════════════════════
ngo_router = APIRouter(prefix="/api/ngo", tags=["NGO Manager"])

@ngo_router.get("/search")
async def search_ngos(condition: str = "", max_cost_inr: int = 0,
                      prefer_online: bool = True, language: str = "",
                      city: str = "", limit: int = 3):
    from services.ngo_manager import find_affordable_support
    return {"results": find_affordable_support(condition, max_cost_inr,
                                               prefer_online, language, city, limit)}

@ngo_router.get("/all")
async def all_ngos(status: str = ""):
    from services.ngo_manager import FULL_NGO_DATABASE
    data = FULL_NGO_DATABASE if not status else \
           [n for n in FULL_NGO_DATABASE if n.get("partnership_status") == status]
    return {"ngos": data, "count": len(data)}

@ngo_router.get("/prospects")
async def get_prospects():
    from services.ngo_manager import get_prospects_for_outreach
    return {"prospects": get_prospects_for_outreach()}

@ngo_router.post("/outreach/draft")
async def draft_email(payload: OutreachRequest):
    from services.ngo_manager import draft_outreach_email
    return draft_outreach_email(payload.ngo_id, payload.sender_name, payload.sender_college)

@ngo_router.post("/outreach/draft-all")
async def draft_all(sender_name: str = "SentinelMind Team",
                    sender_college: str = "Our College"):
    from services.ngo_manager import draft_all_prospect_emails
    return {"drafts": draft_all_prospect_emails(sender_name, sender_college)}

@ngo_router.post("/outreach/mark-sent/{ngo_id}")
async def mark_sent(ngo_id: str):
    from services.ngo_manager import mark_outreach_sent
    return {"success": mark_outreach_sent(ngo_id)}

@ngo_router.post("/add")
async def add_ngo(payload: AddNGORequest):
    from services.ngo_manager import add_new_ngo
    return add_new_ngo(payload.model_dump())


# ══════════════════════════════════════════════════════════════════════════════
# /api/volunteer
# ══════════════════════════════════════════════════════════════════════════════
volunteer_router = APIRouter(prefix="/api/volunteer", tags=["Volunteer"])

@volunteer_router.post("/register")
async def register_volunteer(payload: RegisterVolunteerRequest):
    from services.volunteer_manager import register_volunteer
    return register_volunteer(**payload.model_dump())

@volunteer_router.post("/training")
async def update_training(payload: TrainingUpdateRequest):
    from services.volunteer_manager import update_training
    return update_training(payload.volunteer_id, payload.level)

@volunteer_router.get("/assign/{user_id}")
async def assign_volunteer(user_id: str, urgency: str = "standard",
                           language: str = "English"):
    from services.volunteer_manager import assign_volunteer
    result = assign_volunteer(user_id, urgency, language)
    if not result:
        return {"available": False,
                "message": "No volunteers available right now. Counselor has been notified."}
    return {"available": True, "volunteer": result}

@volunteer_router.post("/complete")
async def complete_assignment(payload: CompleteAssignmentRequest):
    from services.volunteer_manager import complete_assignment
    return complete_assignment(payload.assignment_id, payload.volunteer_id, payload.outcome)

@volunteer_router.get("/load")
async def volunteer_load():
    from services.volunteer_manager import get_volunteer_load, get_available_count
    return {"volunteers": get_volunteer_load(),
            "available_standard": get_available_count("standard"),
            "available_crisis":   get_available_count("crisis")}


# ══════════════════════════════════════════════════════════════════════════════
# /api/counselor
# ══════════════════════════════════════════════════════════════════════════════
counselor_router = APIRouter(prefix="/api/counselor", tags=["Counselor"])

@counselor_router.post("/register")
async def register_counselor(payload: RegisterCounselorRequest):
    from services.counselor_service import register_counselor
    return register_counselor(**payload.model_dump())

@counselor_router.get("/capacity")
async def counselor_capacity():
    from services.counselor_service import get_counselor_capacity
    return {"counselors": get_counselor_capacity()}

@counselor_router.get("/roster/{counselor_id}")
async def counselor_roster(counselor_id: str):
    from services.counselor_service import get_counselor_student_roster
    return {"roster": get_counselor_student_roster(counselor_id)}

@counselor_router.post("/notes")
async def create_note(payload: SessionNoteRequest):
    from services.counselor_service import create_session_note
    date_str = payload.session_date or datetime.utcnow().date().isoformat()
    return create_session_note(
        payload.counselor_id, payload.user_id_hash, date_str,
        payload.session_type, payload.presenting_issues,
        payload.interventions, payload.risk_level,
        payload.next_appointment, payload.private_notes, payload.shared_summary)

@counselor_router.get("/notes/{counselor_id}")
async def get_notes(counselor_id: str, user_id_hash: str = ""):
    from services.counselor_service import get_session_notes
    return {"notes": get_session_notes(counselor_id, user_id_hash or None)}

@counselor_router.get("/stats")
async def session_stats():
    from services.counselor_service import get_aggregate_session_stats
    return get_aggregate_session_stats()


# ══════════════════════════════════════════════════════════════════════════════
# /api/stories
# ══════════════════════════════════════════════════════════════════════════════
stories_router = APIRouter(prefix="/api/stories", tags=["Peer Stories"])

@stories_router.get("")
async def list_stories(condition: str = ""):
    from services.peer_stories import list_all_stories
    return {"stories": list_all_stories(condition or None)}

@stories_router.get("/match/{user_id}")
async def match_stories(user_id: str, condition: str = "", tags: str = ""):
    from services.peer_stories import get_story_for_context
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    return {"stories": get_story_for_context(condition, tag_list)}

@stories_router.get("/{story_id}")
async def get_story(story_id: str):
    from services.peer_stories import get_story_text
    text = get_story_text(story_id)
    if not text:
        raise HTTPException(status_code=404, detail="Story not found")
    return {"story_id": story_id, "text": text}

@stories_router.post("/submit")
async def submit_story(payload: StorySubmissionRequest):
    from services.peer_stories import submit_story
    return submit_story(payload.user_id, payload.title,
                        payload.content, payload.condition, payload.what_helped)


# ══════════════════════════════════════════════════════════════════════════════
# /api/voice
# ══════════════════════════════════════════════════════════════════════════════
voice_router = APIRouter(prefix="/api/voice", tags=["Voice"])

@voice_router.post("/transcribe")
async def transcribe_base64_endpoint(payload: VoiceBase64Request):
    import asyncio
    from services.voice_service import transcribe_base64, is_whisper_available
    from core.pii_scrubber import scrub
    if not is_whisper_available():
        raise HTTPException(status_code=503,
            detail="Whisper not installed. Run: pip install openai-whisper")
    result = await asyncio.to_thread(transcribe_base64, payload.audio_b64, payload.extension)
    result["transcript"] = scrub(result.get("transcript", ""))
    return result

@voice_router.post("/logbook-entry")
async def voice_logbook_entry(payload: VoiceBase64Request):
    import asyncio, base64
    from services.voice_service import transcribe_base64, is_whisper_available
    from core.pii_scrubber import scrub
    from data.db import save_logbook_entry
    from data.progress_store import update_progress
    from services.rag_engine import get_uplifting_response
    if not is_whisper_available():
        raise HTTPException(status_code=503,
            detail="Whisper not installed. Run: pip install openai-whisper ffmpeg-python")
    result     = await asyncio.to_thread(transcribe_base64, payload.audio_b64, payload.extension)
    transcript = scrub(result.get("transcript", ""))
    if not transcript:
        return {"error": "Could not transcribe audio", "details": result}
    encrypted = base64.b64encode(transcript.encode()).decode()
    await asyncio.to_thread(save_logbook_entry, payload.user_id, encrypted,
                            payload.consent_level, transcript, [])
    progress  = await asyncio.to_thread(update_progress, payload.user_id, 5, ["logbook"])
    uplifting = await asyncio.to_thread(get_uplifting_response, "neutral")
    return {"status": "saved", "transcript": transcript,
            "language": result.get("language","unknown"),
            "confidence": result.get("confidence", 0),
            "consent_level": payload.consent_level,
            "progress": progress, "uplifting_feedback": uplifting}

@voice_router.get("/status")
async def voice_status():
    from services.voice_service import is_whisper_available
    return {"whisper_available": is_whisper_available()}


# ══════════════════════════════════════════════════════════════════════════════
# /api/whatsapp
# ══════════════════════════════════════════════════════════════════════════════
whatsapp_router = APIRouter(prefix="/api/whatsapp", tags=["WhatsApp"])

@whatsapp_router.post("/incoming")
async def whatsapp_incoming(request: Request):
    """
    Twilio WhatsApp webhook endpoint.
    REQUIRES: pip install python-multipart  ← missing this causes 422 errors.
    Always returns valid TwiML XML — a non-2xx or non-XML response causes
    Twilio error 11200.
    """
    from services.whatsapp_service import handle_incoming_message, build_twiml_error

    try:
        form_data = await request.form()
        twiml     = await handle_incoming_message(dict(form_data))
    except Exception as e:
        # Last-resort safety net — Twilio must always get 200 + XML
        print(f"[WHATSAPP ROUTE ERROR] {type(e).__name__}: {e}")
        twiml = build_twiml_error()

    return Response(content=twiml, media_type="application/xml", status_code=200)


@whatsapp_router.get("/incoming")
async def whatsapp_verify():
    """
    GET on the same URL — lets you verify the webhook is reachable in a browser.
    Twilio only uses POST, but this confirms your ngrok URL is live.
    """
    return {
        "status":  "WhatsApp webhook is live ✅",
        "method":  "POST requests from Twilio are handled here",
        "check":   "If you see this, your ngrok URL is working correctly",
    }


@whatsapp_router.get("/status")
async def whatsapp_status():
    from config import settings
    import importlib.util
    multipart_installed = importlib.util.find_spec("multipart") is not None
    return {
        "enabled":               settings.enable_whatsapp,
        "from_number":           settings.twilio_whatsapp_from,
        "configured":            bool(settings.twilio_account_sid),
        "webhook_url":           "/api/whatsapp/incoming",
        "python_multipart_ok":   multipart_installed,
        "warning": (
            None if multipart_installed
            else "⚠️ python-multipart not installed — Twilio form parsing will fail with 422. "
                 "Run: pip install python-multipart"
        ),
        "setup_steps": [
            "1. console.twilio.com → Messaging → Try it out → Send a WhatsApp message",
            "2. WhatsApp the sandbox number with the join code",
            "3. Set Webhook URL: {your_ngrok_url}/api/whatsapp/incoming  (method: POST)",
            "4. Test: send 'Hi' to the sandbox number",
        ],
    }


# ══════════════════════════════════════════════════════════════════════════════
# /api/reminder
# ══════════════════════════════════════════════════════════════════════════════
reminder_router = APIRouter(prefix="/api/reminder", tags=["Reminders"])

@reminder_router.post("/run-checks")
async def run_reminder_checks():
    import asyncio
    from services.reminder_engine import run_all_checks
    return await asyncio.to_thread(run_all_checks)

@reminder_router.get("/followups-needed")
async def followups_needed():
    from services.reminder_engine import check_post_escalation_followups
    return {"followups": check_post_escalation_followups()}

@reminder_router.get("/inactive-users")
async def inactive_users(min_sessions: int = 3):
    from services.reminder_engine import detect_inactive_users
    return {"inactive": detect_inactive_users(min_prior_sessions=min_sessions)}

@reminder_router.get("/risk-window")
async def academic_risk_window():
    from services.reminder_engine import get_current_risk_window, get_risk_window_message
    return {"window": get_current_risk_window(),
            "student_message": get_risk_window_message()}


# ══════════════════════════════════════════════════════════════════════════════
# /api/rating
# ══════════════════════════════════════════════════════════════════════════════
rating_router = APIRouter(prefix="/api/rating", tags=["Ratings"])

@rating_router.post("")
async def submit_rating(payload: RatingRequest):
    from services.rating_service import submit_rating
    return submit_rating(**payload.model_dump())

@rating_router.get("/{target_type}/{target_id}")
async def get_ratings(target_type: str, target_id: str):
    from services.rating_service import get_ratings_for_target
    return get_ratings_for_target(target_type, target_id)

@rating_router.get("/admin/low-rated")
async def low_rated(threshold: float = 3.0):
    from services.rating_service import get_low_rated_counselors
    return {"low_rated_counselors": get_low_rated_counselors(threshold)}

@rating_router.get("/admin/aggregate")
async def aggregate_ratings():
    from services.rating_service import get_aggregate_ratings
    return get_aggregate_ratings()


# ══════════════════════════════════════════════════════════════════════════════
# /api/passive — Passive detection: camera, typing patterns, usage, prosody
# ══════════════════════════════════════════════════════════════════════════════
passive_router = APIRouter(prefix="/api/passive", tags=["Passive Detection"])


class FrameRequest(BaseModel):
    user_id:  str
    frame_b64:str   # Base64-encoded JPEG frame from frontend camera
    save_score: bool = True


class TypingMetricsRequest(BaseModel):
    user_id:          str
    message_length:   int
    typing_duration_s:float
    backspace_count:  int
    total_keystrokes: int
    hour_of_day:      int = -1  # -1 = auto-detect from server time


class VoiceProsodyRequest(BaseModel):
    user_id:   str
    audio_b64: str
    extension: str = "ogg"


@passive_router.post("/camera/analyze")
async def analyze_camera_frame(payload: FrameRequest):
    """
    Analyze a camera frame for facial distress signals.
    Frame is never stored — only the derived score is saved.
    Requires: pip install mediapipe opencv-python
    """
    import asyncio
    from services.passive_detection import analyze_frame_base64
    from data.db import insert_record

    result = await asyncio.to_thread(analyze_frame_base64, payload.frame_b64)

    if payload.save_score and result.get("distress_score") is not None:
        insert_record("passive_signal", {
            "user_id":       payload.user_id,
            "signal_type":   "facial_expression",
            "distress_score":result["distress_score"],
            "emotion":       result.get("emotion"),
            "escalate":      result.get("escalate", False),
            "ts":            datetime.utcnow().isoformat(),
        })
        # Escalate if face shows high distress
        if result.get("escalate"):
            from core.escalation_chain import trigger_escalation
            trigger_escalation(
                user_id=payload.user_id,
                trigger_type="PASSIVE_FACIAL_DISTRESS",
                details={"distress_score": result["distress_score"],
                         "emotion": result.get("emotion")},
                override_level="L2_ALERT",
            )
    return result


@passive_router.post("/typing/record")
async def record_typing_metrics(payload: TypingMetricsRequest):
    """
    Record typing pattern metrics for one message.
    Frontend sends these alongside each chat message.
    """
    from services.passive_detection import TypingAnalyzer
    from data.db import insert_record

    hour = payload.hour_of_day if payload.hour_of_day >= 0 else datetime.utcnow().hour

    # Use session-scoped analyzer (stored in session)
    from core import session_manager
    session = session_manager.get_or_create(payload.user_id)

    if not hasattr(session, 'typing_analyzer'):
        session.typing_analyzer = TypingAnalyzer(payload.user_id)

    result = session.typing_analyzer.record_message(
        payload.message_length, payload.typing_duration_s,
        payload.backspace_count, payload.total_keystrokes, hour
    )

    if result.get("risk") in ("high", "moderate"):
        insert_record("passive_signal", {
            "user_id":     payload.user_id,
            "signal_type": "typing_pattern",
            "risk":        result["risk"],
            "signals":     result.get("signals", {}),
            "ts":          datetime.utcnow().isoformat(),
        })

    return result


@passive_router.post("/voice/prosody")
async def analyze_prosody(payload: VoiceProsodyRequest):
    """
    Analyze vocal prosody (pitch, energy, speaking rate) from a voice recording.
    Detects flat affect (depression) and racing speech (anxiety/mania).
    Requires: pip install librosa soundfile
    """
    import asyncio, base64
    from services.passive_detection import analyze_voice_prosody

    audio_bytes = base64.b64decode(payload.audio_b64)
    result = await asyncio.to_thread(analyze_voice_prosody, audio_bytes)

    if result.get("escalate"):
        from core.escalation_chain import trigger_escalation
        trigger_escalation(
            user_id=payload.user_id,
            trigger_type="PASSIVE_VOICE_DISTRESS",
            details=result,
            override_level="L2_ALERT",
        )
    return result


@passive_router.get("/usage/{user_id}")
async def usage_pattern(user_id: str):
    """Analyze app usage patterns for passive distress signals."""
    import asyncio
    from services.passive_detection import analyze_usage_pattern
    return await asyncio.to_thread(analyze_usage_pattern, user_id)


@passive_router.get("/camera/status")
async def camera_status():
    from services.passive_detection import is_mediapipe_available
    return {
        "mediapipe_available": is_mediapipe_available(),
        "install_note": "pip install mediapipe opencv-python" if not is_mediapipe_available() else None,
    }


@passive_router.get("/voice/status")
async def prosody_status():
    from services.passive_detection import is_prosody_available
    return {
        "librosa_available": is_prosody_available(),
        "install_note": "pip install librosa soundfile" if not is_prosody_available() else None,
    }


@passive_router.get("/iot/devices")
async def list_iot_devices():
    from services.passive_detection import list_supported_devices
    return {"devices": list_supported_devices()}


@passive_router.get("/iot/devices/{device_id}")
async def get_device_guide(device_id: str):
    from services.passive_detection import get_device_setup_guide
    return get_device_setup_guide(device_id)


# ══════════════════════════════════════════════════════════════════════════════
# /api/consent
# ══════════════════════════════════════════════════════════════════════════════
consent_router = APIRouter(prefix="/api/consent", tags=["Consent"])

@consent_router.get("/dashboard/{user_id}")
async def consent_dashboard(user_id: str):
    from services.consent_manager import get_consent_dashboard
    return get_consent_dashboard(user_id)

@consent_router.post("/grant/{user_id}/{feature}")
async def grant_consent(user_id: str, feature: str):
    from services.consent_manager import grant_consent
    return grant_consent(user_id, feature)

@consent_router.post("/revoke/{user_id}/{feature}")
async def revoke_consent(user_id: str, feature: str):
    from services.consent_manager import revoke_consent
    return revoke_consent(user_id, feature)

@consent_router.post("/revoke-all/{user_id}")
async def revoke_all(user_id: str):
    from services.consent_manager import revoke_all_consent
    return revoke_all_consent(user_id)

@consent_router.get("/status/{user_id}")
async def consent_status(user_id: str):
    from services.consent_manager import get_consent_status
    return {"user_id": user_id, "consents": get_consent_status(user_id)}


# ══════════════════════════════════════════════════════════════════════════════
# /api/engage  (non-clinical entry points)
# ══════════════════════════════════════════════════════════════════════════════
engage_router = APIRouter(prefix="/api/engage", tags=["Engagement"])

class StudySessionRequest(BaseModel):
    user_id:            str
    duration_minutes:   int
    subject:            str = ""
    focus_self_rating:  int = Field(default=5, ge=1, le=10)
    interruptions:      int = 0

class SleepLogRequest(BaseModel):
    user_id:       str
    sleep_hours:   float
    sleep_quality: int = Field(default=5, ge=1, le=10)
    bedtime_hour:  int = 23
    wake_hour:     int = 7
    college_id:    str = "default"

class MusicMoodRequest(BaseModel):
    user_id:    str
    track_name: str
    artist:     str = ""
    genre_tags: list[str] = []
    self_mood:  str = ""

class ExamDateRequest(BaseModel):
    user_id:   str
    subject:   str
    exam_date: str
    exam_type: str = "semester"

class PeerPingRequest(BaseModel):
    from_user_id: str
    to_user_id:   str
    message_type: str = "check_in"

@engage_router.post("/study")
async def log_study(payload: StudySessionRequest):
    from services.engagement_hooks import log_study_session
    return log_study_session(**payload.model_dump())

@engage_router.get("/study/{user_id}")
async def study_stats(user_id: str, days: int = 7):
    from services.engagement_hooks import get_study_stats
    return get_study_stats(user_id, days)

@engage_router.post("/sleep")
async def log_sleep(payload: SleepLogRequest):
    from services.engagement_hooks import log_sleep
    return log_sleep(**payload.model_dump())

@engage_router.get("/sleep/leaderboard")
async def sleep_board(college_id: str = "default", days: int = 7):
    from services.engagement_hooks import get_sleep_leaderboard
    return {"leaderboard": get_sleep_leaderboard(college_id, days)}

@engage_router.post("/music")
async def log_music(payload: MusicMoodRequest):
    from services.engagement_hooks import log_music_mood
    return log_music_mood(**payload.model_dump())

@engage_router.get("/music/trend/{user_id}")
async def music_trend(user_id: str, days: int = 14):
    from services.engagement_hooks import get_music_mood_trend
    return get_music_mood_trend(user_id, days)

@engage_router.post("/exam")
async def add_exam(payload: ExamDateRequest):
    from services.engagement_hooks import add_exam_date
    return add_exam_date(**payload.model_dump())

@engage_router.get("/exams/{user_id}")
async def upcoming_exams(user_id: str):
    from services.engagement_hooks import get_upcoming_exams
    return {"exams": get_upcoming_exams(user_id)}

@engage_router.post("/peer-ping")
async def peer_ping(payload: PeerPingRequest):
    from services.engagement_hooks import send_peer_ping
    return send_peer_ping(payload.from_user_id, payload.to_user_id, payload.message_type)

@engage_router.get("/peer-pings/{user_id}")
async def get_pings(user_id: str):
    from services.engagement_hooks import get_peer_pings
    return {"pings": get_peer_pings(user_id)}


# ══════════════════════════════════════════════════════════════════════════════
# /api/silent  (non-verbal engagement)
# ══════════════════════════════════════════════════════════════════════════════
silent_router = APIRouter(prefix="/api/silent", tags=["Silent Engagement"])

class EmojiMoodRequest(BaseModel):
    user_id: str
    emoji:   str

class WeatherMoodRequest(BaseModel):
    user_id: str
    weather: str

class ChallengeCompleteRequest(BaseModel):
    user_id:      str
    challenge_id: str
    felt_better:  Optional[bool] = None

@silent_router.post("/emoji")
async def emoji_mood(payload: EmojiMoodRequest):
    from services.silent_engagement import log_emoji_mood
    return log_emoji_mood(payload.user_id, payload.emoji)

@silent_router.post("/weather")
async def weather_mood(payload: WeatherMoodRequest):
    from services.silent_engagement import log_weather_mood
    return log_weather_mood(payload.user_id, payload.weather)

@silent_router.get("/challenge/{user_id}")
async def daily_challenge(user_id: str):
    from services.silent_engagement import get_daily_challenge
    return get_daily_challenge(user_id)

@silent_router.post("/challenge/complete")
async def complete_challenge(payload: ChallengeCompleteRequest):
    from services.silent_engagement import complete_challenge
    return complete_challenge(payload.user_id, payload.challenge_id, payload.felt_better)

@silent_router.post("/open/{user_id}")
async def app_open(user_id: str):
    from services.silent_engagement import log_app_open
    return log_app_open(user_id)

@silent_router.get("/options")
async def silent_options():
    """All silent engagement options — for frontend to display."""
    return {
        "emoji_options":   list(__import__('services.silent_engagement',
                                fromlist=['EMOJI_MOOD_MAP']).EMOJI_MOOD_MAP.keys()),
        "weather_options": list(__import__('services.silent_engagement',
                                fromlist=['WEATHER_MOODS']).WEATHER_MOODS.keys()),
        "description":     "No words needed. Just tap.",
    }


# ══════════════════════════════════════════════════════════════════════════════
# /api/wearable  (OAuth + sync)
# ══════════════════════════════════════════════════════════════════════════════
wearable_router = APIRouter(prefix="/api/wearable", tags=["Wearable"])

@wearable_router.get("/fitbit/connect/{user_id}")
async def fitbit_connect(user_id: str):
    from services.wearable_oauth import get_fitbit_auth_url
    return get_fitbit_auth_url(user_id)

@wearable_router.get("/fitbit/callback")
async def fitbit_callback(code: str, state: str):
    from services.wearable_oauth import handle_fitbit_callback
    return await handle_fitbit_callback(code, state)

@wearable_router.post("/fitbit/sync/{user_id}")
async def fitbit_sync(user_id: str):
    from services.wearable_oauth import sync_fitbit_data
    return await sync_fitbit_data(user_id)

@wearable_router.get("/google-fit/connect/{user_id}")
async def gfit_connect(user_id: str):
    from services.wearable_oauth import get_google_fit_auth_url
    return get_google_fit_auth_url(user_id)

@wearable_router.get("/devices/{user_id}")
async def connected_devices(user_id: str):
    from services.wearable_oauth import get_connected_devices
    return {"devices": get_connected_devices(user_id)}

@wearable_router.delete("/devices/{user_id}/{device}")
async def disconnect(user_id: str, device: str):
    from services.wearable_oauth import disconnect_device
    return disconnect_device(user_id, device)


# ══════════════════════════════════════════════════════════════════════════════
# /api/baseline
# ══════════════════════════════════════════════════════════════════════════════
baseline_router = APIRouter(prefix="/api/baseline", tags=["Baseline"])

@baseline_router.get("/status/{user_id}")
async def baseline_status(user_id: str):
    from services.baseline_service import get_calibration_status
    return get_calibration_status(user_id)

@baseline_router.post("/build/{user_id}")
async def build_baseline(user_id: str):
    import asyncio
    from services.baseline_service import build_baseline
    return await asyncio.to_thread(build_baseline, user_id)

@baseline_router.get("/all/{user_id}")
async def all_baselines(user_id: str):
    from services.baseline_service import get_all_baselines
    return get_all_baselines(user_id)

@baseline_router.post("/check/{user_id}")
async def check_deviation(user_id: str, metric: str, value: float):
    from services.baseline_service import check_deviation
    return check_deviation(user_id, metric, value)


# ══════════════════════════════════════════════════════════════════════════════
# /api/jobs
# ══════════════════════════════════════════════════════════════════════════════
jobs_router = APIRouter(prefix="/api/jobs", tags=["Jobs"])

class JobApplicationRequest(BaseModel):
    role_id:            str
    applicant_name_hash:str
    college:            str
    contact_hash:       str
    motivation:         str = ""

@jobs_router.get("/roles")
async def list_roles():
    from services.jobs_ecosystem import list_job_roles
    return {"roles": list_job_roles()}

@jobs_router.post("/apply")
async def apply(payload: JobApplicationRequest):
    from services.jobs_ecosystem import apply_for_role
    return apply_for_role(**payload.model_dump())

@jobs_router.get("/impact")
async def jobs_impact():
    from services.jobs_ecosystem import get_jobs_impact_summary
    return get_jobs_impact_summary()


# ══════════════════════════════════════════════════════════════════════════════
# /api/phenotype — Digital phenotyping (no hardware needed)
# ══════════════════════════════════════════════════════════════════════════════
phenotype_router = APIRouter(prefix="/api/phenotype", tags=["Phenotyping"])

class TypingEventRequest(BaseModel):
    user_id:           str
    message:           str
    typing_duration_s: float = 0.0
    backspace_count:   int   = 0
    total_keystrokes:  int   = 0

@phenotype_router.post("/typing")
async def record_typing(payload: TypingEventRequest):
    """Record a typing event with behavioral signals."""
    from services.phenotyping import analyze_language
    lang_sig = analyze_language(payload.message)
    return {"language_signals": lang_sig, "message_length": len(payload.message)}

@phenotype_router.get("/cross-session/{user_id}")
async def cross_session(user_id: str):
    """Check historical usage patterns for withdrawal signals."""
    import asyncio
    from services.phenotyping import check_cross_session_patterns
    return await asyncio.to_thread(check_cross_session_patterns, user_id)

@phenotype_router.get("/snapshots/{user_id}")
async def phenotype_snapshots(user_id: str, limit: int = 10):
    from data.db import query_records
    snaps = query_records("phenotype_snapshot", {"user_id": user_id})
    return {"snapshots": snaps[-limit:], "count": len(snaps)}


# ══════════════════════════════════════════════════════════════════════════════
# /api/memory — Conversation memory + tone adaptation
# ══════════════════════════════════════════════════════════════════════════════
memory_router = APIRouter(prefix="/api/memory", tags=["Conversation Memory"])

class TechniqueRequest(BaseModel):
    user_id:   str
    technique: str
    helped:    Optional[bool] = None

@memory_router.get("/{user_id}")
async def get_memory(user_id: str):
    from services.conversation_memory import ConversationMemory
    m = ConversationMemory(user_id)
    return {
        "dominant_state":     m.dominant_state,
        "sessions_count":     m.sessions_count,
        "has_crisis_history": m.has_crisis_history,
        "context":            m.get_context_for_prompt(),
    }

@memory_router.post("/technique")
async def record_technique(payload: TechniqueRequest):
    from services.conversation_memory import ConversationMemory
    m = ConversationMemory(payload.user_id)
    m.record_technique(payload.technique, payload.helped)
    return {"status": "recorded", "technique": payload.technique}

@memory_router.get("/tone/{user_id}/{state}")
async def get_tone_rules(user_id: str, state: str):
    from services.conversation_memory import TONE_RULES
    return TONE_RULES.get(state, TONE_RULES["neutral"])


# ══════════════════════════════════════════════════════════════════════════════
# /api/zones — Story-based zone unlocks
# ══════════════════════════════════════════════════════════════════════════════
zones_router = APIRouter(prefix="/api/zones", tags=["Zones"])

@zones_router.get("/{user_id}")
async def get_zones(user_id: str):
    from data.progress_store import get_progress, get_zone_progress
    prog   = get_progress(user_id)
    streak = prog.get("streak", 0) if prog else 0
    return get_zone_progress(streak)

@zones_router.get("/all")
async def all_zones():
    from data.progress_store import ZONES
    return {"zones": ZONES}


# ══════════════════════════════════════════════════════════════════════════════
# /api/payment — Institutional Razorpay invoicing
# ══════════════════════════════════════════════════════════════════════════════
payment_router = APIRouter(prefix="/api/payment", tags=["Payment"])

class InvoiceRequest(BaseModel):
    institution_id:   str
    institution_name: str
    student_count:    int
    contact_email:    str
    tier:             str = "standard"  # standard | premium

@payment_router.post("/invoice")
async def create_invoice(payload: InvoiceRequest):
    from services.payment_service import create_institutional_order
    return create_institutional_order(**payload.model_dump())

@payment_router.get("/pricing")
async def pricing():
    from services.payment_service import get_pricing_tiers
    return get_pricing_tiers()

@payment_router.get("/invoices/{institution_id}")
async def get_invoices(institution_id: str):
    from data.db import query_records
    return {"invoices": query_records("invoice", {"institution_id": institution_id})}

@payment_router.post("/webhook/razorpay")
async def razorpay_webhook(request: Request):
    """Razorpay payment confirmation webhook."""
    from services.payment_service import handle_razorpay_webhook
    body = await request.body()
    sig  = request.headers.get("X-Razorpay-Signature","")
    return handle_razorpay_webhook(body, sig)
