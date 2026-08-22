"""
services/iot_adapter.py — Production IoT Adapter with Motion Artifact Filtering.

POINT 5 of 7: Noise-robust IoT that handles real messy wearable data.

Mode 1: Single-point threshold (simple, good for demos)
Mode 2: Rolling window + motion filter + baseline deviation (production-grade)

WHY MOTION FILTERING:
  A student running for a bus shows HR=160. Same as a panic attack.
  Without filtering, both trigger a crisis alert. With accelerometer data,
  we discard HR readings taken during high movement (>2g acceleration).
  The real signal is: elevated HR WITH low movement = emotional arousal.
"""
import random
import statistics
from collections import deque
from datetime import datetime
from config import settings
from data.db import save_iot_reading, insert_record

# Rolling window buffers per user per metric (Mode 2)
_rolling_buffers: dict[str, dict[str, deque]] = {}


def _get_buffer(user_id: str, metric: str) -> deque:
    if user_id not in _rolling_buffers:
        _rolling_buffers[user_id] = {}
    if metric not in _rolling_buffers[user_id]:
        _rolling_buffers[user_id][metric] = deque(maxlen=settings.iot_rolling_window)
    return _rolling_buffers[user_id][metric]


def process_reading(user_id: str, metric_type: str, value: float) -> dict:
    """Mode 1 path: single-point threshold check."""
    ts = datetime.utcnow().isoformat()
    breached, msg = _check_absolute_threshold(metric_type, value)
    save_iot_reading(user_id, metric_type, value, ts, breached, motion_filtered=False)
    result = {"user_id": user_id, "metric_type": metric_type,
              "value": value, "ts": ts, "threshold_breached": breached,
              "alert_message": msg, "unit": _unit(metric_type), "mode": "absolute"}
    if breached:
        _escalate(user_id, metric_type, value, ts, msg)
    return result


def process_reading_with_filter(user_id: str, metric_type: str, value: float,
                                 accelerometer_g: float = 0.0) -> dict:
    """
    Mode 2 path: motion filter + rolling window + baseline deviation.

    accelerometer_g: combined acceleration in g-force from the wearable.
                     0.0 = stationary, >2.0 = running/vigorous activity.
                     Pass 0.0 if no accelerometer available (disables filter).
    """
    ts = datetime.utcnow().isoformat()

    # Step 1: Motion artifact filter
    motion_filtered = False
    if (metric_type == "heart_rate" and
            accelerometer_g > settings.iot_motion_threshold and
            accelerometer_g > 0.0):
        # High motion — discard this HR reading as artifact
        save_iot_reading(user_id, metric_type, value, ts,
                         threshold_breached=False, motion_filtered=True)
        return {"user_id": user_id, "metric_type": metric_type, "value": value,
                "ts": ts, "motion_filtered": True,
                "note": f"Discarded: motion={accelerometer_g:.1f}g > threshold={settings.iot_motion_threshold}g",
                "threshold_breached": False}

    # Step 2: Add to rolling window
    buf = _get_buffer(user_id, metric_type)
    buf.append(value)

    # Step 3: Only alert if window is full (avoids single-spike false positives)
    if len(buf) < settings.iot_rolling_window:
        save_iot_reading(user_id, metric_type, value, ts, False, False)
        return {"user_id": user_id, "metric_type": metric_type, "value": value,
                "ts": ts, "rolling_buffer_filling": True,
                "readings_needed": settings.iot_rolling_window - len(buf)}

    rolling_mean = statistics.mean(buf)
    rolling_std  = statistics.stdev(buf) if len(buf) > 1 else 0.0

    # Step 4: Check against personal baseline (Mode 2) or absolute threshold
    from services.baseline_service import check_deviation
    baseline_result = check_deviation(user_id, metric_type, rolling_mean)

    # Also check absolute threshold as safety net
    abs_breached, abs_msg = _check_absolute_threshold(metric_type, rolling_mean)

    # Alert fires if EITHER baseline deviation OR absolute threshold breached
    breached = baseline_result.get("alert", False) or abs_breached
    msg = baseline_result.get("context", abs_msg) if breached else ""

    save_iot_reading(user_id, metric_type, rolling_mean, ts, breached, False)

    result = {
        "user_id":       user_id,
        "metric_type":   metric_type,
        "raw_value":     value,
        "rolling_mean":  round(rolling_mean, 2),
        "rolling_std":   round(rolling_std, 2),
        "ts":            ts,
        "motion_filtered": False,
        "threshold_breached": breached,
        "alert_message": msg,
        "baseline":      baseline_result,
        "unit":          _unit(metric_type),
        "mode":          "rolling_baseline",
    }

    if breached:
        _escalate(user_id, metric_type, rolling_mean, ts, msg)

        # Update rolling baseline after confirmed alert (Mode 2 adaptive)
        from services.baseline_service import update_baseline_rolling
        update_baseline_rolling(user_id, metric_type, value)

    return result


def _check_absolute_threshold(metric: str, value: float) -> tuple[bool, str]:
    """Clinical absolute thresholds — safety net regardless of mode."""
    thresholds = {
        "heart_rate":  (settings.iot_heart_rate_low,  settings.iot_heart_rate_high),
        "spo2":        (settings.iot_spo2_low,         101.0),
        "sleep_hours": (settings.iot_sleep_low_hours,  14.0),
        "gsr":         (0.0,                           settings.iot_gsr_high),
    }
    lo, hi = thresholds.get(metric, (0, 9999))
    if value > hi:
        return True, f"⚠️ High {metric.replace('_',' ')}: {value}{_unit(metric)} (>{hi})"
    if value < lo:
        return True, f"⚠️ Low {metric.replace('_',' ')}: {value}{_unit(metric)} (<{lo})"
    return False, ""


def simulate_reading(user_id: str, metric_type: str, profile: str = "normal") -> dict:
    """Generate realistic simulated reading (Mode 1 testing)."""
    profiles = {
        "normal":  {"heart_rate":(62,88), "spo2":(96,99), "gsr":(0.2,1.5), "sleep_hours":(6.5,8.5)},
        "stressed":{"heart_rate":(100,145),"spo2":(93,96),"gsr":(2.0,5.0), "sleep_hours":(3.0,5.5)},
        "panic":   {"heart_rate":(140,180),"spo2":(88,93),"gsr":(5.0,10.0),"sleep_hours":(1.0,4.0)},
    }
    lo, hi = profiles.get(profile, profiles["normal"]).get(metric_type, (60,100))
    value  = round(random.uniform(lo, hi), 2)

    if settings.is_business:
        # Simulate accelerometer: panic profile = low motion (emotional not physical)
        accel = 0.1 if profile == "panic" else random.uniform(0.0, 1.5)
        return process_reading_with_filter(user_id, metric_type, value, accel)
    return process_reading(user_id, metric_type, value)


def simulate_all_metrics(user_id: str, profile: str = "normal") -> list:
    return [simulate_reading(user_id, m, profile)
            for m in ["heart_rate", "spo2", "gsr", "sleep_hours"]]


def get_biometric_summary(user_id: str) -> dict:
    from data.db import get_iot_readings
    summary = {}
    for metric in ["heart_rate", "spo2", "sleep_hours", "gsr"]:
        readings = get_iot_readings(user_id, metric_type=metric)
        values   = [r["value"] for r in readings if isinstance(r.get("value"),(int,float))]
        if values:
            summary[metric] = {
                "count":  len(values),
                "mean":   round(sum(values)/len(values), 2),
                "min":    round(min(values), 2),
                "max":    round(max(values), 2),
                "alerts": sum(1 for r in readings if r.get("threshold_breached")),
                "motion_filtered": sum(1 for r in readings if r.get("motion_filtered")),
            }
    return summary


def _escalate(user_id: str, metric: str, value: float, ts: str, msg: str):
    print(f"[IoT ALERT] {msg}")
    try:
        from core.merkle_ledger import log_event
        from core.escalation_chain import trigger_escalation
        log_event(user_id, "IOT_THRESHOLD_BREACH",
                  {"metric": metric, "value": value, "ts": ts, "alert": msg},
                  notify_counselor=True)
        trigger_escalation(user_id, "IOT_THRESHOLD_BREACH",
                           {"metric": metric, "value": value, "alert": msg},
                           override_level="L2_ALERT")
    except Exception as e:
        print(f"[IoT] Escalation error: {e}")


def _unit(metric: str) -> str:
    return {"heart_rate":"bpm","spo2":"%","gsr":"μS","sleep_hours":"h"}.get(metric,"")
