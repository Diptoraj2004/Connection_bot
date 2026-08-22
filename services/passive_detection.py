"""
services/passive_detection.py — Passive & Visual Signal Detection Engine.

WHY THIS EXISTS:
  Many students in distress will NOT answer 9 PHQ-9 questions honestly.
  They may type "I'm fine" while their face shows distress, their typing
  is erratic, or they haven't opened the app in days.

  This module provides detection signals that work WITHOUT requiring
  explicit answers — making the system useful even when students can't
  or won't express how they're feeling directly.

WHAT IT DETECTS:
  1. FACIAL EXPRESSION ANALYSIS (optional, camera-based)
     - Uses MediaPipe FaceMesh landmarks (runs locally, no cloud)
     - Detects: brow furrow, lip compression, eye openness, gaze aversion
     - Maps to: anxiety, sadness, anger, neutral, distress
     - Privacy: frames never stored or transmitted — only derived scores

  2. TYPING PATTERN ANALYSIS
     - Keystroke dynamics: pause duration, backspace rate, message length trend
     - Long pauses → possible dissociation or rumination
     - Very short messages after long ones → withdrawal signal
     - High backspace rate → self-censorship (saying then unsaying)

  3. APP USAGE PATTERNS
     - Session time of day (3am usage = sleep disruption signal)
     - Session frequency drop (was daily, now absent = withdrawal)
     - Feature avoidance (opens app, reads, closes without typing)

  4. VOICE PROSODY (from WhatsApp voice notes)
     - Speaking rate, pitch variance, energy levels
     - Flat affect (low variance) → possible depression
     - Racing speech → possible mania/anxiety

REAL DEVICE INTEGRATION:
  - Fitbit SDK: https://dev.fitbit.com/build/reference/
  - Apple HealthKit: via health_kit_bridge.py
  - Google Fit REST API: https://developers.google.com/fit
  - Garmin Connect IQ: https://developer.garmin.com/connect-iq/
  - Mi Band / Xiaomi: via gadgetbridge protocol (open source)

PRIVACY DESIGN:
  - Camera frames: processed locally, NEVER stored or sent
  - Only the derived emotion score (0.0–1.0) is saved, not the frame
  - Typing patterns: aggregated per session, not per keystroke
  - All passive signals require explicit user opt-in per feature
"""

from datetime import datetime, time as dt_time
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# 1. FACIAL EXPRESSION ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def analyze_frame_base64(frame_b64: str, user_id: str = "") -> dict:
    """
    Analyze a single camera frame for facial expressions.
    Frame is processed locally — never stored or transmitted.

    Returns emotion scores (0.0–1.0) and a composite distress score.

    REAL IMPLEMENTATION uses MediaPipe FaceMesh + landmark geometry:
      pip install mediapipe opencv-python

    Current implementation: placeholder that returns structure.
    Replace the _analyze_landmarks() function with real MediaPipe code.
    """
    # Consent gate — never analyze without explicit opt-in
    if user_id:
        from services.consent_manager import has_consent
        if not has_consent(user_id, "camera_analysis"):
            return {"available": False, "error": "Camera analysis not consented to.",
                    "consent_url": "/api/consent/grant"}
    try:
        import base64, numpy as np
        frame_bytes = base64.b64decode(frame_b64)

        # Try real MediaPipe analysis
        try:
            result = _analyze_with_mediapipe(frame_bytes)
        except ImportError:
            result = _placeholder_analysis()

        return result

    except Exception as e:
        return {"error": str(e), "distress_score": None, "available": False}


def _analyze_with_mediapipe(frame_bytes: bytes) -> dict:
    """
    Real facial analysis using MediaPipe FaceMesh.
    Detects landmark geometry to infer emotional state.
    Install: pip install mediapipe opencv-python
    """
    import cv2
    import mediapipe as mp
    import numpy as np

    mp_face = mp.solutions.face_mesh
    face_mesh = mp_face.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
    )

    # Decode frame
    nparr  = np.frombuffer(frame_bytes, np.uint8)
    frame  = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = face_mesh.process(rgb)

    if not result.multi_face_landmarks:
        return {"face_detected": False, "distress_score": None,
                "message": "No face detected — ensure camera is visible"}

    lm = result.multi_face_landmarks[0].landmark
    h, w = frame.shape[:2]

    def pt(idx): return np.array([lm[idx].x * w, lm[idx].y * h])

    # ── Brow furrow (corrugator supercilii) ───────────────────────────────────
    # Landmarks: 107, 336 (inner brow), 9 (nose bridge)
    left_brow_inner  = pt(107)
    right_brow_inner = pt(336)
    nose_bridge      = pt(9)
    brow_distance    = np.linalg.norm(left_brow_inner - right_brow_inner)
    brow_to_nose     = np.linalg.norm(left_brow_inner - nose_bridge)
    furrow_ratio     = brow_distance / max(brow_to_nose, 1)
    # Lower ratio → more furrowed → more distress
    furrow_score = max(0.0, min(1.0, 1.0 - furrow_ratio / 2.0))

    # ── Eye openness ──────────────────────────────────────────────────────────
    # Upper/lower lid landmarks: 159/145 (left), 386/374 (right)
    left_eye_h  = abs(pt(159)[1] - pt(145)[1])
    right_eye_h = abs(pt(386)[1] - pt(374)[1])
    eye_w_ref   = abs(pt(33)[0]  - pt(133)[0])   # Eye width reference
    eye_openness = ((left_eye_h + right_eye_h) / 2) / max(eye_w_ref, 1)
    # Very low openness = sleepy/depressed, very high = wide-eyed anxiety
    eye_distress = 1.0 - min(eye_openness / 0.3, 1.0)

    # ── Lip compression ───────────────────────────────────────────────────────
    upper_lip = pt(13)
    lower_lip = pt(14)
    lip_dist  = abs(upper_lip[1] - lower_lip[1])
    mouth_w   = abs(pt(61)[0] - pt(291)[0])
    lip_ratio = lip_dist / max(mouth_w, 1)
    # Compressed lips (low ratio) → tension/suppression
    lip_score = max(0.0, min(1.0, 1.0 - lip_ratio * 4))

    # ── Composite distress score ─────────────────────────────────────────────
    distress = (furrow_score * 0.45 + eye_distress * 0.35 + lip_score * 0.20)

    # Map to emotion labels
    if distress > 0.65:
        emotion = "high_distress"
    elif distress > 0.40:
        emotion = "mild_distress"
    elif distress > 0.20:
        emotion = "neutral"
    else:
        emotion = "calm"

    face_mesh.close()

    return {
        "face_detected":   True,
        "distress_score":  round(distress, 3),
        "emotion":         emotion,
        "components": {
            "brow_furrow":    round(furrow_score, 3),
            "eye_openness":   round(eye_distress, 3),
            "lip_compression":round(lip_score, 3),
        },
        "escalate":        distress > 0.65,
        "note":            "Scores derived from facial geometry only. Not diagnostic.",
        "privacy":         "Frame not stored. Only this score dict is saved.",
    }


def _placeholder_analysis() -> dict:
    """Returned when MediaPipe not installed — informs frontend gracefully."""
    return {
        "face_detected":  None,
        "distress_score": None,
        "emotion":        "unavailable",
        "available":      False,
        "install_note":   "pip install mediapipe opencv-python to enable facial analysis",
        "escalate":       False,
    }


def is_mediapipe_available() -> bool:
    try:
        import mediapipe  # noqa
        import cv2        # noqa
        return True
    except ImportError:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# 2. TYPING PATTERN ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

class TypingAnalyzer:
    """
    Tracks typing patterns within a session to detect distress signals.

    Frontend sends keystroke timing data with each message.
    The student never sees this analysis — it runs silently.
    """

    def __init__(self, user_id: str):
        self.user_id          = user_id
        self.message_lengths: list[int]   = []
        self.pause_durations: list[float] = []  # seconds between keystrokes
        self.backspace_rates: list[float] = []  # backspaces / total keystrokes
        self.session_times:   list[int]   = []  # hour of day (0-23)

    def record_message(self, message_length: int, typing_duration_s: float,
                       backspace_count: int, total_keystrokes: int,
                       hour_of_day: int) -> dict:
        """
        Record typing metrics for one message. Returns current risk signals.
        """
        self.message_lengths.append(message_length)
        self.session_times.append(hour_of_day)

        # Typing speed (chars per second)
        if typing_duration_s > 0 and message_length > 0:
            chars_per_sec = message_length / typing_duration_s
        else:
            chars_per_sec = 0.0

        # Pause duration (average seconds per character)
        avg_pause = typing_duration_s / max(message_length, 1)
        self.pause_durations.append(avg_pause)

        # Backspace rate
        bsp_rate = backspace_count / max(total_keystrokes, 1)
        self.backspace_rates.append(bsp_rate)

        return self._assess()

    def _assess(self) -> dict:
        if len(self.message_lengths) < 2:
            return {"signals": {}, "risk": "insufficient_data"}

        signals = {}

        # Late-night usage (1am–5am)
        if self.session_times:
            last_hour = self.session_times[-1]
            if 1 <= last_hour <= 5:
                signals["late_night_usage"] = True

        # Flag a sharp drop in message length vs. the recent average
        if len(self.message_lengths) >= 4:
            avg_prev = sum(self.message_lengths[:-2]) / (len(self.message_lengths) - 2)
            avg_now  = sum(self.message_lengths[-2:]) / 2
            if avg_prev > 20 and avg_now < 5:
                signals["message_length_collapse"] = True

        # High backspace rate (self-censorship)
        if self.backspace_rates:
            avg_bsp = sum(self.backspace_rates) / len(self.backspace_rates)
            if avg_bsp > 0.25:  # 1 in 4 keystrokes is backspace
                signals["high_self_censorship"] = True

        # Very slow typing (>8 sec per char on average) = possible dissociation
        if self.pause_durations:
            avg_pause = sum(self.pause_durations) / len(self.pause_durations)
            if avg_pause > 8.0:
                signals["very_slow_typing"] = True

        # Very fast typing with short messages = possible manic episode
        if len(self.pause_durations) >= 3:
            recent_pause = sum(self.pause_durations[-3:]) / 3
            recent_len   = sum(self.message_lengths[-3:]) / 3
            if recent_pause < 0.5 and recent_len < 10:
                signals["rapid_short_messages"] = True

        risk = "low"
        if len(signals) >= 3:
            risk = "high"
        elif len(signals) >= 1:
            risk = "moderate"

        return {
            "signals":          signals,
            "risk":             risk,
            "message_count":    len(self.message_lengths),
            "avg_backspace_rate": round(
                sum(self.backspace_rates) / max(len(self.backspace_rates), 1), 3),
        }


# ─────────────────────────────────────────────────────────────────────────────
# 3. VOICE PROSODY ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def analyze_voice_prosody(audio_bytes: bytes) -> dict:
    """
    Analyze vocal features from a WhatsApp voice note or logbook recording.
    Uses librosa for pitch/energy extraction.

    Detects:
      - Flat affect (very low pitch variance) → possible depression
      - Racing speech (very high speaking rate) → anxiety/mania
      - Low energy / soft voice → low arousal state

    Install: pip install librosa soundfile
    """
    try:
        import io
        import numpy as np
        import librosa
        import soundfile as sf

        audio_file = io.BytesIO(audio_bytes)
        try:
            y, sr = librosa.load(audio_file, sr=16000, mono=True)
        except Exception:
            return {"available": False, "error": "Could not decode audio"}

        if len(y) < sr * 0.5:  # Less than 0.5 seconds
            return {"available": False, "error": "Audio too short for analysis"}

        # ── Pitch (F0) extraction ─────────────────────────────────────────────
        f0, voiced_flag, _ = librosa.pyin(y, fmin=80, fmax=400, sr=sr)
        voiced_f0 = f0[voiced_flag]

        if len(voiced_f0) < 10:
            pitch_mean, pitch_std = 0.0, 0.0
        else:
            pitch_mean = float(np.nanmean(voiced_f0))
            pitch_std  = float(np.nanstd(voiced_f0))

        # ── Energy / RMS ──────────────────────────────────────────────────────
        rms       = librosa.feature.rms(y=y)[0]
        energy    = float(np.mean(rms))
        energy_db = float(librosa.amplitude_to_db(np.array([energy]))[0])

        # ── Speaking rate proxy (zero-crossing rate) ──────────────────────────
        zcr      = librosa.feature.zero_crossing_rate(y)[0]
        avg_zcr  = float(np.mean(zcr))

        # ── Duration ─────────────────────────────────────────────────────────
        duration_s = len(y) / sr

        # ── Score mapping ─────────────────────────────────────────────────────
        # Flat affect: pitch_std < 15 Hz in a voiced recording
        flat_affect    = pitch_std < 15.0 and pitch_mean > 0
        # Racing speech: very high ZCR relative to duration
        racing_speech  = avg_zcr > 0.15
        # Low energy: below -40dB
        low_energy     = energy_db < -40.0

        distress_indicators = sum([flat_affect, racing_speech, low_energy])
        distress_score = min(distress_indicators / 3.0, 1.0)

        return {
            "available":           True,
            "duration_seconds":    round(duration_s, 1),
            "pitch_mean_hz":       round(pitch_mean, 1),
            "pitch_variance_hz":   round(pitch_std, 1),
            "energy_db":           round(energy_db, 1),
            "speaking_rate_proxy": round(avg_zcr, 4),
            "flat_affect":         flat_affect,
            "racing_speech":       racing_speech,
            "low_energy":          low_energy,
            "distress_score":      round(distress_score, 3),
            "escalate":            distress_score >= 0.67,
            "note":                "Prosody analysis is indicative only. Not diagnostic.",
        }

    except ImportError:
        return {
            "available":   False,
            "error":       "librosa not installed",
            "install_note":"pip install librosa soundfile",
        }
    except Exception as e:
        return {"available": False, "error": str(e)}


def is_prosody_available() -> bool:
    try:
        import librosa  # noqa
        return True
    except ImportError:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# 4. APP USAGE PATTERN ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def analyze_usage_pattern(user_id: str) -> dict:
    """
    Analyze session timing and frequency patterns for passive distress signals.
    Uses existing chat history from DB — no extra data collection needed.
    """
    from data.db import get_chat_history
    from datetime import datetime, timedelta

    history = get_chat_history(user_id, limit=50)
    if len(history) < 5:
        return {"risk": "insufficient_data", "signals": {}}

    signals = {}
    session_hours = []
    session_dates = []

    for msg in history:
        if msg.get("role") != "user":
            continue
        ts_str = msg.get("_ts", "")
        try:
            ts = datetime.fromisoformat(ts_str)
            session_hours.append(ts.hour)
            session_dates.append(ts.date())
        except ValueError:
            pass

    if not session_hours:
        return {"risk": "insufficient_data", "signals": {}}

    # Late-night sessions (1am–5am)
    late_night_count = sum(1 for h in session_hours if 1 <= h <= 5)
    if late_night_count >= 2:
        signals["repeated_late_night_usage"] = {
            "count": late_night_count,
            "meaning": "Multiple late-night sessions may indicate sleep disruption",
        }

    # Usage frequency drop
    if len(session_dates) >= 6:
        from collections import Counter
        date_counts = Counter(session_dates)
        all_dates   = sorted(date_counts.keys())
        recent      = sum(date_counts[d] for d in all_dates[-3:])
        previous    = sum(date_counts[d] for d in all_dates[-6:-3])
        if previous > 0 and recent < previous * 0.3:
            signals["usage_frequency_drop"] = {
                "recent_sessions":   recent,
                "previous_sessions": previous,
                "meaning": "Session frequency dropped significantly — possible withdrawal",
            }

    # Clustering (many sessions in short period)
    if len(session_dates) >= 4:
        recent_dates = sorted(session_dates)[-4:]
        date_span = (recent_dates[-1] - recent_dates[0]).days
        if date_span <= 1 and len(recent_dates) >= 4:
            signals["crisis_clustering"] = {
                "sessions_in_24h": len(recent_dates),
                "meaning": "4+ sessions within 24 hours — possible acute crisis",
            }

    risk = "low"
    if len(signals) >= 2:
        risk = "high"
    elif len(signals) == 1:
        risk = "moderate"

    return {
        "user_id":       user_id,
        "signals":       signals,
        "risk":          risk,
        "analyzed_msgs": len(session_hours),
        "hours_active":  list(set(session_hours)),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 5. REAL IOT DEVICE INTEGRATION SPECS
# ─────────────────────────────────────────────────────────────────────────────

REAL_IOT_DEVICES = {
    "fitbit": {
        "name":         "Fitbit (Charge/Sense/Versa series)",
        "api_docs":     "https://dev.fitbit.com/build/reference/web-api/",
        "metrics":      ["heart_rate", "sleep_stages", "spo2", "stress_score", "hrv"],
        "auth":         "OAuth 2.0",
        "free_tier":    True,
        "setup_steps": [
            "1. Register app at dev.fitbit.com → Create App",
            "2. Set OAuth callback URL to {your_url}/api/iot/fitbit/callback",
            "3. Add FITBIT_CLIENT_ID and FITBIT_CLIENT_SECRET to .env",
            "4. Student links Fitbit via /api/iot/fitbit/connect/{user_id}",
        ],
        "code_example": """
import requests

def get_fitbit_heart_rate(access_token: str, date: str = 'today') -> dict:
    url = f'https://api.fitbit.com/1/user/-/activities/heart/date/{date}/1d/1min.json'
    r = requests.get(url, headers={'Authorization': f'Bearer {access_token}'})
    return r.json()
""",
    },
    "apple_healthkit": {
        "name":         "Apple HealthKit (iPhone/Apple Watch)",
        "api_docs":     "https://developer.apple.com/documentation/healthkit",
        "metrics":      ["heart_rate", "hrv", "sleep_analysis", "spo2",
                         "steps", "mindful_minutes", "respiratory_rate"],
        "auth":         "iOS entitlements (no server-side auth)",
        "free_tier":    True,
        "note":         "Requires iOS native app — React Native bridge available",
        "setup_steps": [
            "1. Enable HealthKit capability in your iOS app Xcode project",
            "2. Request permissions in Info.plist (NSHealthShareUsageDescription)",
            "3. Use HKHealthStore to query samples",
            "4. Send to backend: POST /api/iot/reading with metric_type and value",
        ],
        "code_example": """
// React Native (using react-native-health)
import AppleHealthKit from 'react-native-health';

const permissions = {
  permissions: {
    read: [AppleHealthKit.Constants.Permissions.HeartRate,
           AppleHealthKit.Constants.Permissions.SleepAnalysis]
  }
};

AppleHealthKit.initHealthKit(permissions, (err) => {
  AppleHealthKit.getHeartRateSamples({period: 60}, (err, results) => {
    // POST results to /api/iot/reading
  });
});
""",
    },
    "google_fit": {
        "name":         "Google Fit API (Android/Wear OS)",
        "api_docs":     "https://developers.google.com/fit/rest/v1/reference",
        "metrics":      ["heart_rate", "sleep", "activity", "calories", "steps"],
        "auth":         "OAuth 2.0 (Google Cloud Console)",
        "free_tier":    True,
        "setup_steps": [
            "1. Enable Fitness API in Google Cloud Console",
            "2. Create OAuth 2.0 credentials",
            "3. Add GOOGLE_FIT_CLIENT_ID to .env",
            "4. Student authorizes via /api/iot/google-fit/connect/{user_id}",
        ],
        "code_example": """
import requests

def get_google_fit_heart_rate(access_token: str) -> list:
    url = 'https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate'
    body = {
        'aggregateBy': [{'dataTypeName': 'com.google.heart_rate.bpm'}],
        'bucketByTime': {'durationMillis': 3600000},
        'startTimeMillis': int((time.time() - 86400) * 1000),
        'endTimeMillis': int(time.time() * 1000),
    }
    r = requests.post(url, json=body,
                      headers={'Authorization': f'Bearer {access_token}'})
    return r.json().get('bucket', [])
""",
    },
    "garmin": {
        "name":         "Garmin Connect IQ / Health SDK",
        "api_docs":     "https://developer.garmin.com/health-api/overview/",
        "metrics":      ["heart_rate", "stress_level", "hrv", "spo2",
                         "sleep_score", "body_battery"],
        "auth":         "OAuth 2.0 (Garmin Developer Portal)",
        "free_tier":    True,
        "note":         "body_battery is Garmin-exclusive — excellent fatigue proxy",
    },
    "mi_band": {
        "name":         "Xiaomi Mi Band / Smart Band (GadgetBridge)",
        "api_docs":     "https://codeberg.org/Freeyourgadget/Gadgetbridge",
        "metrics":      ["heart_rate", "sleep", "steps", "spo2"],
        "auth":         "Bluetooth LE (no cloud API needed)",
        "free_tier":    True,
        "note":         "Most affordable wearable in India (₹2000–4000). "
                        "Use GadgetBridge (open source) to extract data without Xiaomi cloud.",
        "india_note":   "Mi Band 7/8 Pro widely available on Flipkart/Amazon India",
    },
}


def get_device_setup_guide(device_key: str) -> dict:
    device = REAL_IOT_DEVICES.get(device_key)
    if not device:
        return {"error": f"Unknown device: {device_key}",
                "available": list(REAL_IOT_DEVICES.keys())}
    return device


def list_supported_devices() -> list:
    return [{"id": k, "name": v["name"], "metrics": v["metrics"],
             "free_tier": v.get("free_tier", True)}
            for k, v in REAL_IOT_DEVICES.items()]
