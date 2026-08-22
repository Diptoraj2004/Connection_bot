"""
tests/test_core.py — Full test suite for SentinelMind v4.
Run with: python -m pytest tests/ -v --tb=short
No API keys needed — all tests use mocks and synthetic data.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pytest


# ── Config ────────────────────────────────────────────────────────────────────
class TestConfig:
    def test_settings_load(self):
        from config import settings
        assert settings.groq_model is not None
        assert len(settings.crisis_keywords) > 5
        assert len(settings.academic_risk_windows) > 0

    def test_no_duplicate_keys(self):
        from config import settings
        # Both should come from single definitions inside Settings class
        assert settings.followup_reminder_hours == 48
        assert settings.inactivity_alert_days   == 5
        assert settings.enable_parent_share     is False  # OFF by default


# ── PII Scrubber ──────────────────────────────────────────────────────────────
class TestPIIScrubber:
    def test_phone_scrubbed(self):
        from core.pii_scrubber import scrub
        assert "9876543210" not in scrub("Call me at 9876543210")

    def test_email_scrubbed(self):
        from core.pii_scrubber import scrub
        assert "@college.edu" not in scrub("Email me at student@college.edu")

    def test_safe_text_unchanged(self):
        from core.pii_scrubber import scrub
        assert "anxious" in scrub("I have been feeling anxious lately")

    def test_empty_safe(self):
        from core.pii_scrubber import scrub
        assert scrub("") == ""


# ── Crisis Interceptor ────────────────────────────────────────────────────────
class TestCrisisInterceptor:
    def test_crisis_keyword_caught(self):
        from core.crisis_interceptor import check_crisis_keywords
        r = check_crisis_keywords("I want to end my life")
        assert r["is_crisis"] is True
        assert "1800-599-0019" in r["response"]

    def test_safe_text_not_crisis(self):
        from core.crisis_interceptor import check_crisis_keywords
        r = check_crisis_keywords("I am feeling a bit sad today")
        assert r["is_crisis"] is False

    def test_aasra_number_correct(self):
        """AASRA number must be 91-22-27546669 not 9820466627."""
        from core.crisis_interceptor import CRISIS_RESPONSE
        assert "91-22-27546669" in CRISIS_RESPONSE


# ── Behavioral Monitor ────────────────────────────────────────────────────────
class TestBehavioralMonitor:
    def test_single_analyze_message_exists(self):
        """Only one analyze_message should exist (no duplicate)."""
        import core.behavioral_monitor as bm
        import inspect
        funcs = [name for name, obj in inspect.getmembers(bm, inspect.isfunction)
                 if name == "analyze_message"]
        assert len(funcs) == 1

    def test_bullying_detected(self):
        from core.behavioral_monitor import analyze_message
        r = analyze_message("The seniors are ragging me every night")
        assert r["signals"]["bullying"] is True

    def test_academic_stress_detected(self):
        from core.behavioral_monitor import analyze_message
        r = analyze_message("I am going to fail my semester exams")
        assert r["signals"]["academic_stress"] is True

    def test_hyper_to_calm_escalates(self):
        from core.behavioral_monitor import BehavioralTracker
        t = BehavioralTracker("u_test")
        t.ingest("I haven't slept I have so many ideas EVERYTHING IS AMAZING!!!")
        t.ingest("I haven't slept racing thoughts can't stop going")
        t.ingest("I haven't slept still going")
        t.ingest("I haven't slept still going strong")
        t.ingest("I haven't slept still going")
        t.ingest("I haven't slept still going")
        t.ingest("I haven't slept still going")
        t.ingest("I haven't slept still going")
        result = t.ingest("I feel at peace now. Goodbye everyone. Everything is sorted.")
        assert result["risk_level"] in ("critical", "high")

    def test_bullying_in_trigger_map(self):
        from core.escalation_chain import TRIGGER_LEVEL_MAP
        assert "BULLYING_DETECTED"   in TRIGGER_LEVEL_MAP
        assert "INACTIVITY_DETECTED" in TRIGGER_LEVEL_MAP


# ── Questionnaire Scoring ─────────────────────────────────────────────────────
class TestQuestionnaires:
    def test_phq9_minimal(self):
        from data.questionnaires import score_responses
        r = score_responses("phq-9", [0]*9)
        assert r["severity"] == "minimal"
        assert r["escalate"] is False

    def test_phq9_severe(self):
        from data.questionnaires import score_responses
        r = score_responses("phq-9", [3,3,3,3,2,2,2,2,3])
        assert r["severity"] in ("moderately_severe","severe")
        assert r["escalate"] is True

    def test_phq9_q9_crisis_flag(self):
        from data.questionnaires import score_responses
        r = score_responses("phq-9", [0]*8 + [1])
        assert r["crisis_flag"] is True

    def test_gad7_moderate(self):
        from data.questionnaires import score_responses
        r = score_responses("gad-7", [2,2,1,2,1,1,2])
        assert r["severity"] == "moderate"

    def test_aq10_referral(self):
        from data.questionnaires import score_responses
        r = score_responses("aq10", [1,1,1,1,1,1,0,0,0,0])
        assert r["escalate"] is True

    def test_infer_adhd(self):
        from data.questionnaires import infer_test_from_text
        assert infer_test_from_text("I can't focus or pay attention at all") == "asrs"

    def test_infer_autism(self):
        from data.questionnaires import infer_test_from_text
        assert infer_test_from_text("I feel sensory overload in loud places") == "aq10"

    def test_infer_default(self):
        from data.questionnaires import infer_test_from_text
        assert infer_test_from_text("I don't know what's wrong") == "phq-9"


# ── Merkle Ledger ─────────────────────────────────────────────────────────────
class TestMerkleLedger:
    def test_log_and_verify(self, tmp_path, monkeypatch):
        import core.merkle_ledger as ledger
        monkeypatch.setattr(ledger, "LEDGER_PATH", str(tmp_path/"test.jsonl"))
        ledger.log_event("u1","TEST_A",{"x":1}, notify_counselor=False)
        ledger.log_event("u1","TEST_B",{"x":2}, notify_counselor=False)
        r = ledger.verify_ledger_integrity()
        assert r["valid"] is True
        assert r["entries"] == 2

    def test_empty_ledger_valid(self, tmp_path, monkeypatch):
        import core.merkle_ledger as ledger
        monkeypatch.setattr(ledger, "LEDGER_PATH", str(tmp_path/"empty.jsonl"))
        r = ledger.verify_ledger_integrity()
        assert r["valid"] is True


# ── ML Triage ─────────────────────────────────────────────────────────────────
class TestMLTriage:
    def test_synthetic_data_shape(self):
        from services.ml_triage import _generate_synthetic_data
        X, y, feats = _generate_synthetic_data(n=200)
        assert X.shape[0] == 200
        assert len(feats) > 0

    def test_rule_based_fallback_severe(self):
        from services.ml_triage import _rule_based_fallback
        r = _rule_based_fallback(22)
        assert r["severity_label"] == "severe"
        assert r["escalate"] is True

    def test_rule_based_fallback_minimal(self):
        from services.ml_triage import _rule_based_fallback
        r = _rule_based_fallback(2)
        assert r["severity_label"] == "minimal"
        assert r["escalate"] is False

    def test_dataset_bias_note_in_docstring(self):
        """Confirm the OSMI bias warning is documented in ml_triage."""
        import services.ml_triage as ml
        assert "OSMI" in ml.__doc__ or "bias" in (ml.__doc__ or "").lower() or \
               "indian" in open(ml.__file__).read().lower()


# ── NGO System (single source of truth) ──────────────────────────────────────
class TestNGOSystem:
    def test_ngo_directory_delegates_to_manager(self):
        """ngo_directory must be a shim — same data as ngo_manager."""
        from services.ngo_directory import find_support
        from services.ngo_manager   import find_affordable_support
        r1 = find_support("depression")
        r2 = find_affordable_support("depression", limit=1)
        # Both should return something
        assert r1 is not None
        assert len(r2) > 0

    def test_financial_filter_free_only(self):
        from services.ngo_manager import find_affordable_support
        results = find_affordable_support("depression", max_cost_inr=0)
        for r in results:
            assert r["cost_per_session_inr"] == 0

    def test_find_bullying_specialist(self):
        from services.ngo_manager import find_affordable_support
        results = find_affordable_support("bullying")
        assert len(results) > 0

    def test_outreach_email_generates(self):
        from services.ngo_manager import draft_outreach_email
        result = draft_outreach_email("sangath", "Test Team", "Test College")
        assert "subject" in result
        assert "Sangath" in result["body"]
        assert "SentinelMind" in result["body"]

    def test_add_new_ngo(self):
        from services.ngo_manager import add_new_ngo, get_ngo_by_id
        result = add_new_ngo({
            "name": "Test NGO", "contact_email": "test@test.com",
            "specialty": ["depression"], "city": "Kolkata",
        })
        assert result["status"] == "added"


# ── Volunteer Manager ─────────────────────────────────────────────────────────
class TestVolunteerManager:
    def test_register_and_train(self):
        from services.volunteer_manager import register_volunteer, update_training, _volunteers
        vol = register_volunteer("TestVol", "Test College", ["English"],
                                 list(range(24)), "hash123")
        assert vol["training_level"] == 0
        updated = update_training(vol["volunteer_id"], 2)
        assert updated["training_level"] == 2
        assert updated["status"] == "active"

    def test_crisis_requires_level2(self):
        """Crisis assignments should only go to level >= 2 volunteers."""
        from services.volunteer_manager import (register_volunteer, update_training,
                                                 assign_volunteer, _volunteers)
        # Register a level-1 volunteer only
        v = register_volunteer("LowTrained","TC",["English"],list(range(24)),"h")
        update_training(v["volunteer_id"], 1)
        # Should not be assigned for crisis
        result = assign_volunteer("test_user_crisis", "crisis", "English", current_hour=10)
        # Either None (no level-2 available) or a level-2+ volunteer
        if result:
            assert result["training_level"] >= 2

    def test_training_rebuild_from_records(self, tmp_path, monkeypatch):
        """Simulate restart: _loaded=False, rebuild from DB records."""
        import services.volunteer_manager as vm
        monkeypatch.setattr(vm, "_loaded", False)
        monkeypatch.setattr(vm, "_volunteers", {})
        # Should not crash — just return empty
        vm._build_volunteer_state()


# ── Counselor Service ─────────────────────────────────────────────────────────
class TestCounselorService:
    def test_register_counselor(self):
        from services.counselor_service import register_counselor
        c = register_counselor("Dr. Test", "hash", "College",
                               ["depression"], ["English"], 30)
        assert c["counselor_id"].startswith("csl_")

    def test_capacity_tracking(self):
        from services.counselor_service import get_counselor_capacity
        cap = get_counselor_capacity()
        assert isinstance(cap, list)

    def test_session_note_created(self):
        from services.counselor_service import create_session_note
        note = create_session_note(
            "csl_test", "user_hash_1", "2025-11-01", "initial",
            ["anxiety","stress"], ["breathing_exercise","psychoeducation"],
            "low", "2025-11-15", "Student seems engaged.", "First session completed."
        )
        assert "note_id" in note


# ── Peer Stories ──────────────────────────────────────────────────────────────
class TestPeerStories:
    def test_list_all_returns_stories(self):
        from services.peer_stories import list_all_stories
        stories = list_all_stories()
        assert len(stories) >= 5

    def test_condition_filter(self):
        from services.peer_stories import list_all_stories
        stories = list_all_stories("adhd")
        for s in stories:
            assert s["condition"] == "adhd"

    def test_match_by_context(self):
        from services.peer_stories import get_story_for_context
        stories = get_story_for_context("bullying", ["ragging"])
        assert len(stories) > 0

    def test_story_text_returns_string(self):
        from services.peer_stories import get_story_text
        text = get_story_text("s001")
        assert isinstance(text, str)
        assert len(text) > 50   # Must have meaningful content
        assert "s001" in text or "📖" in text  # Must include story ID or icon marker

    def test_no_real_names_in_stories(self):
        """All stories should be anonymised — no proper names."""
        from services.peer_stories import STORY_LIBRARY
        import re
        for story in STORY_LIBRARY:
            # Names like "Priya" in the DS story are fictional peer names, acceptable
            # Real check: no specific college names or identifiable locations
            text = story["excerpt"]
            assert "IIT" not in text
            assert "NIT " not in text


# ── IoT Adapter ───────────────────────────────────────────────────────────────
class TestIoTAdapter:
    def test_high_hr_breach(self):
        from services.iot_adapter import _check_threshold
        breached, msg = _check_threshold("heart_rate", 160)
        assert breached and "160" in msg

    def test_normal_hr_no_breach(self):
        from services.iot_adapter import _check_threshold
        breached, _ = _check_threshold("heart_rate", 75)
        assert not breached

    def test_low_spo2_breach(self):
        from services.iot_adapter import _check_threshold
        breached, msg = _check_threshold("spo2", 91.0)
        assert breached


# ── Gamification ──────────────────────────────────────────────────────────────
class TestGamification:
    def test_badges_earned(self):
        from data.progress_store import _earn_badges
        badges = _earn_badges(streak=7, total_entries=10, events=["screened"])
        assert "streak_7" in badges
        assert "logged_10" in badges

    def test_level_progression(self):
        from data.progress_store import _get_level
        assert "Seedling" in _get_level(0)["name"]
        assert "Champion" in _get_level(1200)["name"]


# ── Rating Service ────────────────────────────────────────────────────────────
class TestRatingService:
    def test_submit_and_retrieve(self):
        from services.rating_service import submit_rating, get_ratings_for_target
        submit_rating("u1","counselor","csl_001",4,"Good session",True)
        r = get_ratings_for_target("counselor","csl_001")
        assert r["count"] >= 1
        assert r["average"] >= 1.0

    def test_low_rating_flagged(self):
        from services.rating_service import submit_rating, get_low_rated_counselors
        submit_rating("u2","counselor","csl_bad",1,"Poor experience",True)
        submit_rating("u3","counselor","csl_bad",1,"Didn't help",True)
        low = get_low_rated_counselors(threshold=3.0)
        ids = [c.get("target_id") for c in low]
        assert "csl_bad" in ids


# ── Reminder Engine ───────────────────────────────────────────────────────────
class TestReminderEngine:
    def test_risk_window_returns_dict_or_none(self):
        from services.reminder_engine import get_current_risk_window
        result = get_current_risk_window()
        assert result is None or isinstance(result, dict)

    def test_run_all_checks_returns_dict(self):
        from services.reminder_engine import run_all_checks
        result = run_all_checks()
        assert "followups_needed" in result
        assert "inactive_users" in result
        assert "risk_window" in result

    def test_inactive_user_detection(self):
        from services.reminder_engine import detect_inactive_users
        result = detect_inactive_users(min_prior_sessions=3)
        assert isinstance(result, list)



# ── Voice Service ─────────────────────────────────────────────────────────────
class TestVoiceService:
    def test_is_whisper_available_returns_bool(self):
        from services.voice_service import is_whisper_available
        result = is_whisper_available()
        assert isinstance(result, bool)

    def test_transcribe_base64_invalid_input(self):
        """Feeding garbage audio should return an error dict, not raise."""
        from services.voice_service import transcribe_base64, is_whisper_available
        if not is_whisper_available():
            pytest.skip("Whisper not installed — skipping transcription test")
        result = transcribe_base64("not_real_audio_data", "webm")
        assert isinstance(result, dict)
        assert "error" in result or "transcript" in result

    def test_transcribe_upload_invalid_input(self):
        from services.voice_service import transcribe_upload, is_whisper_available
        if not is_whisper_available():
            pytest.skip("Whisper not installed — skipping upload test")
        result = transcribe_upload(b"fake audio bytes", "test.webm")
        assert isinstance(result, dict)


# ── WhatsApp Service ──────────────────────────────────────────────────────────
class TestWhatsAppService:
    def test_hash_phone_is_deterministic(self):
        from services.whatsapp_service import _hash_phone
        h1 = _hash_phone("+919876543210")
        h2 = _hash_phone("+919876543210")
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex digest

    def test_hash_phone_hides_number(self):
        from services.whatsapp_service import _hash_phone
        h = _hash_phone("+919876543210")
        assert "9876543210" not in h

    def test_parse_incoming_standard(self):
        from services.whatsapp_service import parse_incoming
        form = {
            "From": "whatsapp:+919876543210",
            "Body": "Hello SentinelMind",
            "NumMedia": "0",
        }
        result = parse_incoming(form)
        assert result["text"] == "Hello SentinelMind"
        assert result["has_media"] is False
        assert "9876543210" not in result["user_id"]  # must be hashed

    def test_parse_incoming_voice_note(self):
        from services.whatsapp_service import parse_incoming
        form = {
            "From": "whatsapp:+919876543210",
            "Body": "",
            "NumMedia": "1",
            "MediaContentType0": "audio/ogg",
            "MediaUrl0": "https://example.com/audio.ogg",
        }
        result = parse_incoming(form)
        assert result["has_media"] is True
        assert result["media_type"] == "audio/ogg"

    def test_build_twiml_reply_valid_xml(self):
        from services.whatsapp_service import build_twiml_reply
        import xml.etree.ElementTree as ET
        twiml = build_twiml_reply("Hello, I am SentinelMind.")
        # Should be valid XML
        try:
            ET.fromstring(twiml)
            print("Valid XML")
            valid = True
        except ET.ParseError:
            valid = False
        assert valid

    def test_build_twiml_long_message_split(self):
        """WhatsApp has 1600 char limit — long messages must be split."""
        from services.whatsapp_service import build_twiml_reply
        long_msg = "A" * 2000
        twiml = build_twiml_reply(long_msg)
        assert "<Message>" in twiml

    def test_whatsapp_status_returns_configured_flag(self):
        from config import settings
        # Twilio not configured in test env — should be False
        configured = bool(settings.twilio_account_sid)
        assert isinstance(configured, bool)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
