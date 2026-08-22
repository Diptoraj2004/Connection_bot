"""
services/consent_manager.py — Granular Consent Dashboard.

WHY: Students will only accept passive monitoring if they have full,
understandable control over it. Transparency = trust = engagement.

Each feature requires explicit opt-in. Students can revoke at any time.
Revocation is logged to the Merkle Ledger for accountability.

POINT 1 of 7: Passive Consent Dashboard
"""
import uuid
from datetime import datetime
from data.db import insert_record, query_records, get_latest
from config import settings

# ── Consent feature definitions ───────────────────────────────────────────────

CONSENT_FEATURES = {
    "iot_monitoring": {
        "label":       "Wearable Health Monitoring",
        "description": "Heart rate, SpO2, sleep, and stress data from your smartwatch or fitness band.",
        "why":         "Helps detect physical signs of stress or crisis even when you can't express it in words.",
        "data_stored": "Aggregated readings and threshold alerts only. Raw data never retained.",
        "can_revoke":  True,
        "required":    False,
    },
    "camera_analysis": {
        "label":       "Facial Expression Detection",
        "description": "Your camera briefly analyzes facial expressions during check-ins.",
        "why":         "Facial patterns can reveal distress that words don't capture.",
        "data_stored": "Only a distress score (0–1). The camera frame is NEVER stored or sent anywhere.",
        "can_revoke":  True,
        "required":    False,
    },
    "voice_prosody": {
        "label":       "Voice Tone Analysis",
        "description": "When you send voice messages, we analyze pitch, speed, and energy — not the words.",
        "why":         "Voice tone changes with depression, anxiety, and mania in clinically measurable ways.",
        "data_stored": "Acoustic scores only. Your voice recording is processed and discarded immediately.",
        "can_revoke":  True,
        "required":    False,
    },
    "typing_patterns": {
        "label":       "Typing Pattern Analysis",
        "description": "We observe how you type — speed, pauses, and edits — not what you type.",
        "why":         "Typing behavior changes with emotional state (slow + many edits = self-censorship).",
        "data_stored": "Aggregated metrics per message. Individual keystrokes are never stored.",
        "can_revoke":  True,
        "required":    False,
    },
    "usage_patterns": {
        "label":       "App Usage Timing",
        "description": "We notice when you use the app — time of day, frequency, session length.",
        "why":         "Late-night sessions and sudden usage drops are meaningful mental health signals.",
        "data_stored": "Session timestamps and frequency. Message content is separate.",
        "can_revoke":  True,
        "required":    False,
    },
    "parent_share": {
        "label":       "Parent / Guardian Notifications",
        "description": "In Level 4 emergencies, a named guardian is notified.",
        "why":         "Some students want a family member contacted if they are in danger.",
        "data_stored": "Guardian contact stored encrypted. Only triggered in critical emergencies.",
        "can_revoke":  True,
        "required":    False,
        "warning":     "OFF by default. Only enable if you want a family member notified in an emergency.",
    },
    "peer_share": {
        "label":       "Anonymous Peer Story Contribution",
        "description": "Allow your anonymised recovery journey to help other students.",
        "why":         "Peer stories are one of the most effective anti-stigma interventions.",
        "data_stored": "Fully anonymised. No name, college, or identifying details.",
        "can_revoke":  True,
        "required":    False,
    },
}


# ── Consent operations ────────────────────────────────────────────────────────

def get_consent_status(user_id: str) -> dict:
    """Get current consent status for all features."""
    result = get_latest("consent_profile", {"user_id": user_id})
    if result:
        return result.get("consents", {})
    # Default: all passive features off
    return {feature: False for feature in CONSENT_FEATURES}


def grant_consent(user_id: str, feature: str, granted_by: str = "student") -> dict:
    """Grant consent for a specific feature."""
    if feature not in CONSENT_FEATURES:
        return {"error": f"Unknown feature: {feature}"}

    current = get_consent_status(user_id)
    current[feature] = True

    insert_record("consent_profile", {
        "user_id":  user_id,
        "consents": current,
    })

    # Audit log to Merkle Ledger
    _audit_consent_change(user_id, feature, "GRANTED", granted_by)

    return {
        "status":    "granted",
        "feature":   feature,
        "label":     CONSENT_FEATURES[feature]["label"],
        "user_id":   user_id,
        "ts":        datetime.utcnow().isoformat(),
    }


def revoke_consent(user_id: str, feature: str) -> dict:
    """Revoke consent for a specific feature. Effective immediately."""
    if feature not in CONSENT_FEATURES:
        return {"error": f"Unknown feature: {feature}"}

    current = get_consent_status(user_id)
    current[feature] = False

    insert_record("consent_profile", {
        "user_id":  user_id,
        "consents": current,
    })

    _audit_consent_change(user_id, feature, "REVOKED", "student")

    return {
        "status":  "revoked",
        "feature": feature,
        "label":   CONSENT_FEATURES[feature]["label"],
        "note":    "This feature is now disabled. Any previously collected data is retained per our data policy.",
    }


def revoke_all_consent(user_id: str) -> dict:
    """Revoke all consent — nuclear option, GDPR-style."""
    all_revoked = {feature: False for feature in CONSENT_FEATURES}
    insert_record("consent_profile", {
        "user_id":  user_id,
        "consents": all_revoked,
    })
    _audit_consent_change(user_id, "ALL", "REVOKED_ALL", "student")
    return {"status": "all_revoked", "note": "All passive monitoring disabled."}


def has_consent(user_id: str, feature: str) -> bool:
    """Check if a specific feature is consented to. Used as gate in all passive services."""
    if feature not in settings.consent_required_features:
        return True  # Feature doesn't require consent
    status = get_consent_status(user_id)
    return status.get(feature, False)


def get_consent_dashboard(user_id: str) -> dict:
    """Return full consent dashboard for the student-facing UI."""
    current = get_consent_status(user_id)
    history = query_records("consent_audit", {"user_id": user_id})[-10:]

    features_display = []
    for key, meta in CONSENT_FEATURES.items():
        features_display.append({
            "feature_id":  key,
            "label":       meta["label"],
            "description": meta["description"],
            "why":         meta["why"],
            "data_stored": meta["data_stored"],
            "enabled":     current.get(key, False),
            "can_revoke":  meta["can_revoke"],
            "required":    meta["required"],
            "warning":     meta.get("warning"),
        })

    return {
        "user_id":        user_id,
        "features":       features_display,
        "recent_changes": history,
        "your_rights": [
            "You can disable any feature at any time.",
            "Disabling a feature stops ALL new data collection for that feature immediately.",
            "Your previously collected data is retained for 30 days after revocation.",
            "You can request complete data deletion by contacting your institution.",
            "This system complies with India's Digital Personal Data Protection Act 2023.",
        ],
    }


def _audit_consent_change(user_id: str, feature: str, action: str, actor: str):
    """Log consent changes to both DB and Merkle Ledger."""
    insert_record("consent_audit", {
        "user_id": user_id,
        "feature": feature,
        "action":  action,
        "actor":   actor,
        "ts":      datetime.utcnow().isoformat(),
    })
    try:
        from core.merkle_ledger import log_event
        log_event(user_id, f"CONSENT_{action}",
                  {"feature": feature, "actor": actor},
                  notify_counselor=False)
    except Exception:
        pass
