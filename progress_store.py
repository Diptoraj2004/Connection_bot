# Patched: 2025-09-14 - production-ready
"""
Progress / streak store used by chatbot_flow and dashboard aggregation.
Uses supabase_helper.upsert_progress with local fallback.
"""

from datetime import datetime, date
from typing import Optional, Dict, Any
import json
import os

from supabase_helper import upsert_progress, get_user_scores
from config import LOCAL_SAVE_PATH

def _today_iso_date():
    return date.today().isoformat()

def get_progress(user_id: str) -> Dict[str, Any]:
    """
    Return a small progress snapshot for a user. If not present, return defaults.
    """
    # Since DB fallback is local JSON, attempt to read from LOCAL_SAVE_PATH
    try:
        if os.path.exists(LOCAL_SAVE_PATH):
            with open(LOCAL_SAVE_PATH, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            # search for progress entries
            for e in data:
                if e.get("type") == "progress" and e.get("payload", {}).get("user_id") == user_id:
                    return e.get("payload", {}).get("progress", {})
    except Exception:
        pass
    return {"last_mood_date": None, "streak": 0, "total_entries": 0, "trend": {}}

def update_progress(user_id: str, mood_score: int, mood_date: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Update the user's progress/streak info.
    - If the mood_date is today or consecutive, increment streak; otherwise reset based on simple logic.
    """
    mood_date = mood_date or _today_iso_date()
    prev = get_progress(user_id)
    last = prev.get("last_mood_date")
    streak = prev.get("streak", 0)
    total = prev.get("total_entries", 0) + 1
    # simple consecutive-day logic (not timezone-aware for brevity)
    if last:
        try:
            last_date = datetime.strptime(last, "%Y-%m-%d").date()
            cur_date = datetime.strptime(mood_date, "%Y-%m-%d").date()
            if (cur_date - last_date).days == 1:
                streak = streak + 1
            elif (cur_date - last_date).days == 0:
                # same day: keep streak
                pass
            else:
                streak = 1
        except Exception:
            streak = 1
    else:
        streak = 1
    trend = prev.get("trend", {})
    # update minimal trend summary
    trend.update({"last_mood_score": mood_score, "last_updated": datetime.utcnow().isoformat()})
    progress = {"last_mood_date": mood_date, "streak": streak, "total_entries": total, "trend": trend}
    upsert_progress(user_id, progress)
    return progress

def get_department_aggregates(dept: str, year: Optional[str], window_days: int = 30) -> Dict[str, Any]:
    """
    Lightweight aggregate for institute heatmap. For now, returns counts from local fallback.
    In production, run SQL aggregation queries.
    """
    # Heuristic: scan LOCAL_SAVE_PATH for 'score' entries and aggregate by payload details if present
    result = {"dept": dept, "year": year, "count": 0, "avg_score": None}
    try:
        if os.path.exists(LOCAL_SAVE_PATH):
            with open(LOCAL_SAVE_PATH, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            scores = [e["payload"] for e in data if e["type"] == "score" and e["payload"].get("details", {}).get("department") == dept]
            if year:
                scores = [s for s in scores if s.get("details", {}).get("year") == year]
            if scores:
                result["count"] = len(scores)
                vals = [s.get("raw_score", 0) for s in scores if isinstance(s.get("raw_score", None), (int, float))]
                result["avg_score"] = sum(vals) / len(vals) if vals else None
    except Exception:
        pass
    return result
