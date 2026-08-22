"""
services/baseline_service.py — Personal Baseline Calibration Engine.

POINT 2 of 7: 7-day calibration before any alerts fire.

WHY: Every person's normal is different. A resting HR of 95bpm is alarming
for one person, normal for another. Flat affect may be that person's
personality, not depression. Alerting on absolute thresholds without knowing
the person's baseline produces false positives that destroy trust.

HOW IT WORKS:
  - Days 1-7: CALIBRATING — system learns this user's normal ranges.
               No escalation alerts fire. Passive signals collected silently.
  - Day 8+:   ACTIVE — system detects deviations from personal baseline.
               An alert fires when a reading is >1.5 standard deviations
               from this person's calibrated mean.

Mode 1 (Testing): Calibration period = 3 days (faster for demos)
Mode 2 (Business): Calibration period = 7 days (clinically appropriate)
"""
import statistics
from datetime import datetime, timedelta
from typing import Optional
from config import settings
from data.db import insert_record, query_records, get_latest


# ── Calibration period ─────────────────────────────────────────────────────────
CALIBRATION_DAYS = 3 if settings.is_testing else settings.baseline_days
STD_THRESHOLD    = settings.baseline_std_threshold   # 1.5 std devs = alert


# ── Baseline record per user per metric ───────────────────────────────────────

def get_calibration_status(user_id: str) -> dict:
    """
    Returns current calibration state for this user.
    States: calibrating | active | insufficient_data
    """
    profile = get_latest("user_baseline", {"user_id": user_id})
    if not profile:
        # New user — check when they first connected
        first_msg = query_records("chat_message", {"user_id": user_id})
        if not first_msg:
            return {"state": "calibrating", "days_remaining": CALIBRATION_DAYS,
                    "progress_pct": 0, "message": _calibrating_message(CALIBRATION_DAYS)}
        first_ts  = datetime.fromisoformat(first_msg[0]["_ts"])
        days_in   = (datetime.utcnow() - first_ts).days
        remaining = max(0, CALIBRATION_DAYS - days_in)
        pct       = min(100, int((days_in / CALIBRATION_DAYS) * 100))
        if remaining > 0:
            return {"state": "calibrating", "days_remaining": remaining,
                    "progress_pct": pct, "message": _calibrating_message(remaining)}
        # Enough time has passed — build baseline now
        return {"state": "ready_to_calibrate", "days_remaining": 0, "progress_pct": 100}

    return {
        "state":         "active",
        "days_remaining": 0,
        "progress_pct":  100,
        "baselines":     profile.get("baselines", {}),
        "calibrated_at": profile.get("calibrated_at"),
    }


def build_baseline(user_id: str) -> dict:
    """
    Compute and store personal baselines from the last CALIBRATION_DAYS of data.
    Called automatically once calibration period is complete.
    """
    baselines = {}
    metrics   = ["heart_rate", "spo2", "sleep_hours", "gsr",
                 "mood_score", "message_length"]

    for metric in metrics:
        values = _get_metric_values(user_id, metric)
        if len(values) < 3:
            continue
        mean   = statistics.mean(values)
        stdev  = statistics.stdev(values) if len(values) > 1 else 0.0
        baselines[metric] = {
            "mean":     round(mean,  3),
            "stdev":    round(stdev, 3),
            "min":      round(min(values), 3),
            "max":      round(max(values), 3),
            "n_samples":len(values),
            "low_alert":  round(mean - STD_THRESHOLD * max(stdev, 0.01), 3),
            "high_alert": round(mean + STD_THRESHOLD * max(stdev, 0.01), 3),
        }

    record = {
        "user_id":       user_id,
        "baselines":     baselines,
        "calibrated_at": datetime.utcnow().isoformat(),
        "calibration_days": CALIBRATION_DAYS,
    }
    insert_record("user_baseline", record)
    return record


def check_deviation(user_id: str, metric: str, value: float) -> dict:
    """
    Check if a new reading deviates significantly from the personal baseline.

    Returns:
        within_range: bool
        deviation_std: float  (how many std devs from mean)
        alert: bool
        direction: "high" | "low" | "normal"
        context: str  (human-readable interpretation)
    """
    profile = get_latest("user_baseline", {"user_id": user_id})

    # Still calibrating — no alerts
    if not profile:
        status = get_calibration_status(user_id)
        if status["state"] == "calibrating":
            return {"within_range": True, "alert": False,
                    "direction": "calibrating",
                    "context": "Still learning your personal baseline — no alerts yet."}
        elif status["state"] == "ready_to_calibrate":
            build_baseline(user_id)
            return {"within_range": True, "alert": False,
                    "direction": "just_calibrated",
                    "context": "Baseline just built. Monitoring now active."}

    baselines = profile.get("baselines", {})
    b = baselines.get(metric)

    if not b:
        # No baseline for this metric yet — use absolute thresholds
        return _absolute_threshold_check(metric, value)

    mean  = b["mean"]
    stdev = b["stdev"]

    if stdev < 0.001:    # Essentially zero variance
        stdev = mean * 0.1 or 1.0

    deviation = (value - mean) / stdev
    alert     = abs(deviation) > STD_THRESHOLD

    direction = "normal"
    context   = f"Within your normal range ({mean:.1f} ± {stdev:.1f})"

    if deviation > STD_THRESHOLD:
        direction = "high"
        context   = f"Higher than your usual {metric.replace('_',' ')} by {deviation:.1f} standard deviations."
    elif deviation < -STD_THRESHOLD:
        direction = "low"
        context   = f"Lower than your usual {metric.replace('_',' ')} by {abs(deviation):.1f} standard deviations."

    return {
        "metric":         metric,
        "value":          value,
        "personal_mean":  round(mean, 2),
        "deviation_std":  round(deviation, 2),
        "within_range":   not alert,
        "alert":          alert,
        "direction":      direction,
        "context":        context,
        "threshold":      STD_THRESHOLD,
    }


def update_baseline_rolling(user_id: str, metric: str, new_value: float):
    """
    Update the rolling baseline with a new data point.
    Mode 2: Exponential moving average keeps baseline current.
    """
    if not settings.is_business:
        return  # Mode 1 uses static baseline

    profile = get_latest("user_baseline", {"user_id": user_id})
    if not profile:
        return

    baselines = profile.get("baselines", {})
    b = baselines.get(metric)
    if not b:
        return

    # Exponential moving average (alpha=0.1 — slow adaptation)
    alpha      = 0.1
    old_mean   = b["mean"]
    new_mean   = (1 - alpha) * old_mean + alpha * new_value
    # Update rolling variance (Welford-style approximation)
    new_stdev  = max(b["stdev"] * 0.95, abs(new_value - new_mean))

    baselines[metric]["mean"]        = round(new_mean,  3)
    baselines[metric]["stdev"]       = round(new_stdev, 3)
    baselines[metric]["high_alert"]  = round(new_mean + STD_THRESHOLD * new_stdev, 3)
    baselines[metric]["low_alert"]   = round(new_mean - STD_THRESHOLD * new_stdev, 3)

    insert_record("user_baseline", {
        "user_id":       user_id,
        "baselines":     baselines,
        "calibrated_at": profile.get("calibrated_at"),
        "last_updated":  datetime.utcnow().isoformat(),
    })


def get_all_baselines(user_id: str) -> dict:
    """Return full baseline profile for display in student dashboard."""
    status  = get_calibration_status(user_id)
    profile = get_latest("user_baseline", {"user_id": user_id})
    return {
        "user_id":    user_id,
        "status":     status,
        "baselines":  profile.get("baselines", {}) if profile else {},
        "mode":       "personal_deviation" if settings.is_business else "absolute_threshold",
        "note": (
            "Your baselines were built from your first {} days of data. "
            "Alerts fire when readings deviate significantly from YOUR normal, "
            "not from population averages.".format(CALIBRATION_DAYS)
        ),
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _get_metric_values(user_id: str, metric: str) -> list:
    """Pull recent values for a metric from all sources."""
    values = []

    if metric in ("heart_rate", "spo2", "sleep_hours", "gsr"):
        readings = query_records("iot_reading", {"user_id": user_id, "metric_type": metric})
        cutoff   = datetime.utcnow() - timedelta(days=CALIBRATION_DAYS + 2)
        for r in readings:
            try:
                ts = datetime.fromisoformat(r.get("_ts", ""))
                if ts > cutoff:
                    v = r.get("value")
                    if v is not None:
                        values.append(float(v))
            except (ValueError, TypeError):
                pass

    elif metric == "mood_score":
        logs = query_records("mood_log", {"user_id": user_id})
        values = [float(m.get("mood_score", 5)) for m in logs[-50:]]

    elif metric == "message_length":
        msgs = query_records("chat_message", {"user_id": user_id})
        user_msgs = [m for m in msgs if m.get("role") == "user"]
        values    = [float(len(m.get("content", ""))) for m in user_msgs[-50:]]

    return values


def _absolute_threshold_check(metric: str, value: float) -> dict:
    """Fallback to absolute clinical thresholds when no baseline exists."""
    thresholds = {
        "heart_rate":  {"low": settings.iot_heart_rate_low,
                        "high": settings.iot_heart_rate_high},
        "spo2":        {"low": settings.iot_spo2_low,  "high": 100},
        "sleep_hours": {"low": settings.iot_sleep_low_hours, "high": 12},
        "gsr":         {"low": 0, "high": settings.iot_gsr_high},
    }
    t     = thresholds.get(metric, {"low": 0, "high": 999})
    alert = value < t["low"] or value > t["high"]
    direction = "high" if value > t["high"] else ("low" if value < t["low"] else "normal")
    return {
        "metric": metric, "value": value,
        "within_range": not alert, "alert": alert,
        "direction": direction, "deviation_std": None,
        "context": f"Using absolute thresholds (no personal baseline yet). {metric}: {value}",
    }


def _calibrating_message(days_remaining: int) -> str:
    return (
        f"SentinelMind is quietly learning your personal patterns over the next "
        f"{days_remaining} day{'s' if days_remaining != 1 else ''}. "
        f"No alerts will fire during this period — we want to understand YOUR "
        f"normal before flagging anything. Keep using the app naturally."
    )
