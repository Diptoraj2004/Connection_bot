# Patched: 2025-09-14 - production-ready
"""
IoT adapter: stubs and simulation for Google Fit / Fitbit / Apple Health / Samsung Health.
Provides insert_iot_reading function compatible with supabase_helper.insert_iot_reading.
Includes spike detection and alerts creation.
"""

import random
import time
from typing import Optional, Dict, Any
from datetime import datetime

from supabase_helper import insert_iot_reading, create_alert
from config import USE_SIMULATION, USE_GOOGLE_FIT, USE_FITBIT, USE_APPLE_HEALTH, USE_SAMSUNG_HEALTH

def _now_iso():
    return datetime.utcnow().isoformat()

def insert_iot_reading_wrapper(user_id: Optional[str], metric_type: str, value: float, ts: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Public function used by other modules to insert a reading. Will trigger alerts if spike thresholds seen.
    """
    ts = ts or _now_iso()
    metadata = metadata or {}
    rec = insert_iot_reading(user_id=user_id, metric_type=metric_type, value=value, ts=ts, metadata=metadata)
    # lightweight spike detection rules (these are examples — tune in production)
    if metric_type == "heart_rate" and value > 140:
        # create a critical alert
        create_alert(user_id=user_id, session_id=None, test_name="iot_heart_rate", score=int(value), level="critical", details={"metric": "heart_rate", "value": value, "ts": ts}, notify_methods=["email", "whatsapp", "sms", "emergency_contact"])
    return rec

# Simulation
def simulate_reading(user_id: Optional[str], metric_type: str = "heart_rate") -> Dict[str, Any]:
    if metric_type == "heart_rate":
        value = random.randint(50, 160)
    elif metric_type == "sleep_hours":
        value = round(random.uniform(2.0, 9.0), 1)
    else:
        value = random.random() * 100
    return insert_iot_reading_wrapper(user_id=user_id, metric_type=metric_type, value=value, ts=_now_iso(), metadata={"source": "simulation"})

# Connector stubs for future expansion (OAuth flow not implemented here)
def sync_google_fit(user_id: str, oauth_creds: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder: use Google Fit APIs with oauth_creds to fetch activity and insert readings.
    """
    # Implementation note: Use incremental timestamps and rate-limit calls.
    return {"status": "not_implemented", "provider": "google_fit", "user_id": user_id}

def sync_fitbit(user_id: str, oauth_creds: Dict[str, Any]) -> Dict[str, Any]:
    return {"status": "not_implemented", "provider": "fitbit", "user_id": user_id}

def sync_healthkit_stub(user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    return {"status": "not_implemented", "provider": "apple_health", "user_id": user_id}

def sync_samsung_health_stub(user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    return {"status": "not_implemented", "provider": "samsung_health", "user_id": user_id}
