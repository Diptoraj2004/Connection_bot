"""
iot_adapter.py
Stub for smartwatch / smartphone IoT integration.
Currently simulates metrics (replace with real SDKs/APIs later).
"""

import random
from datetime import datetime

def get_sweat_level(user_id):
    # Range: 0 (dry) – 100 (very sweaty)
    return {"user_id": user_id, "sweat_level": random.randint(0, 100), "ts": datetime.now().isoformat()}

def get_oxygen_level(user_id):
    # Range: 85 – 100 (% SpO2)
    return {"user_id": user_id, "oxygen_level": round(random.uniform(90, 100), 1), "ts": datetime.now().isoformat()}

def get_heart_rate(user_id):
    # Range: 50 – 160 bpm
    return {"user_id": user_id, "heart_rate": random.randint(55, 120), "ts": datetime.now().isoformat()}

def get_sleep_data(user_id):
    # Hours slept, quality tag
    hours = round(random.uniform(3, 9), 1)
    quality = "poor" if hours < 5 else ("average" if hours < 7 else "good")
    return {"user_id": user_id, "sleep_hours": hours, "quality": quality, "ts": datetime.now().isoformat()}

def collect_all_metrics(user_id):
    """Return all IoT metrics for a user as a dict"""
    return {
        "sweat": get_sweat_level(user_id),
        "oxygen": get_oxygen_level(user_id),
        "heart": get_heart_rate(user_id),
        "sleep": get_sleep_data(user_id)
    }
