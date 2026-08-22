"""
services/rating_service.py — Rating System for Sessions, Counselors & Resources.

Ratings serve two purposes:
  1. Student agency — they feel heard when feedback is acted on
  2. Quality signal — low-rated counselors/resources get flagged for review

Rating targets:
  - chat_session: Was the AI conversation helpful?
  - counselor_session: How was the human counselor?
  - screening: Did the questionnaire feel right for what you're going through?
  - resource: Was this music/video/guide helpful?
  - peer_volunteer: How was the peer support experience?
"""

from data.db import insert_record, query_records
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────────────
# SUBMIT A RATING
# ─────────────────────────────────────────────────────────────────────────────

def submit_rating(
    user_id: str,
    target_type: str,    # chat_session | counselor_session | screening | resource | peer_volunteer
    target_id: str,      # session_id, counselor_id, test_name, resource_name, volunteer_id
    score: int,          # 1–5
    comment: str = "",
    anonymous: bool = True,
) -> dict:
    """
    Record a rating. Returns the saved record.
    score: 1 = very unhelpful, 5 = very helpful
    """
    if not 1 <= score <= 5:
        return {"error": "Score must be between 1 and 5"}

    record = insert_record("rating", {
        "user_id":     user_id if not anonymous else f"anon_{user_id[:6]}",
        "target_type": target_type,
        "target_id":   target_id,
        "score":       score,
        "comment":     comment[:500],  # Cap comment length
        "anonymous":   anonymous,
        "ts":          datetime.utcnow().isoformat(),
    })

    # Flag for review if score <= 2 on a counselor
    if target_type == "counselor_session" and score <= 2:
        _flag_low_rated_counselor(target_id, score, comment)

    return record


# ─────────────────────────────────────────────────────────────────────────────
# GET RATINGS / AGGREGATE STATS
# ─────────────────────────────────────────────────────────────────────────────

def get_ratings_for_target(target_type: str, target_id: str) -> dict:
    """Get all ratings + average score for a specific target."""
    all_ratings = query_records("rating", {"target_type": target_type, "target_id": target_id})

    if not all_ratings:
        return {"target_type": target_type, "target_id": target_id,
                "count": 0, "average": None, "ratings": []}

    avg = sum(r["score"] for r in all_ratings) / len(all_ratings)
    dist = {str(i): sum(1 for r in all_ratings if r["score"] == i) for i in range(1, 6)}

    return {
        "target_type":   target_type,
        "target_id":     target_id,
        "count":         len(all_ratings),
        "average":       round(avg, 2),
        "distribution":  dist,
        "ratings":       [{"score": r["score"], "comment": r.get("comment", ""),
                           "ts": r.get("_ts", "")} for r in all_ratings],
    }


def get_counselor_ratings(counselor_id: str) -> dict:
    return get_ratings_for_target("counselor_session", counselor_id)


def get_resource_ratings(resource_name: str) -> dict:
    return get_ratings_for_target("resource", resource_name)


def get_aggregate_ratings() -> dict:
    """Admin view — average scores across all target types."""
    all_ratings = query_records("rating")
    if not all_ratings:
        return {"total": 0, "by_type": {}}

    by_type: dict = {}
    for r in all_ratings:
        tt = r.get("target_type", "unknown")
        by_type.setdefault(tt, []).append(r.get("score", 0))

    return {
        "total": len(all_ratings),
        "by_type": {
            tt: {
                "count":   len(scores),
                "average": round(sum(scores) / len(scores), 2),
            }
            for tt, scores in by_type.items()
        },
    }


def get_low_rated_counselors(threshold: float = 3.0) -> list:
    """Return counselors with average rating below threshold."""
    all_ratings = query_records("rating", {"target_type": "counselor_session"})
    counselor_scores: dict = {}
    for r in all_ratings:
        cid = r.get("target_id", "")
        counselor_scores.setdefault(cid, []).append(r.get("score", 0))

    low = []
    for cid, scores in counselor_scores.items():
        avg = sum(scores) / len(scores)
        if avg < threshold:
            low.append({"counselor_id": cid, "average": round(avg, 2), "count": len(scores)})
    return sorted(low, key=lambda x: x["average"])


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL
# ─────────────────────────────────────────────────────────────────────────────

def _flag_low_rated_counselor(counselor_id: str, score: int, comment: str):
    """Log a flag to the audit system when a counselor receives a very low rating."""
    print(f"[RATING] ⚠️  Low rating ({score}/5) for counselor {counselor_id}: {comment[:80]}")
    try:
        from core.merkle_ledger import log_event
        log_event(
            user_id="system",
            event_type="COUNSELOR_LOW_RATING",
            metadata={"counselor_id": counselor_id, "score": score, "comment": comment[:200]},
            notify_counselor=False,
        )
    except Exception as e:
        print(f"[RATING] Ledger error: {e}")
