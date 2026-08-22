"""
core/merkle_ledger.py — Immutable Crisis Audit Ledger.

Every crisis/escalation event is hashed using SHA-256 and chained
(each hash includes the previous hash) to create a tamper-proof audit trail.
This is stored in both the mock DB and an append-only local ledger file.
"""
import hashlib
import json
import os
from datetime import datetime

LEDGER_PATH = "sentinel_crisis_ledger.jsonl"  # Append-only JSONL


def _get_last_hash() -> str:
    """Read the hash of the last ledger entry (genesis block if empty)."""
    if not os.path.exists(LEDGER_PATH):
        return "0" * 64  # Genesis hash

    last_line = ""
    try:
        with open(LEDGER_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    last_line = line
        if last_line:
            return json.loads(last_line).get("hash", "0" * 64)
    except Exception:
        pass
    return "0" * 64


def _hash_event(event_data: str, prev_hash: str) -> str:
    """SHA-256 hash of (event_data + previous_hash)."""
    raw = f"{prev_hash}|{event_data}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def log_event(
    user_id: str,
    event_type: str,
    metadata: dict,
    notify_counselor: bool = True,
) -> dict:
    """
    Append a cryptographically chained event to the ledger.

    event_type examples:
      - "CRISIS_KEYWORD_DETECTED"
      - "IOT_THRESHOLD_BREACH"
      - "SCREENING_ESCALATION"
      - "PHQ9_CRISIS_QUESTION"

    Returns the ledger entry (with hash).
    """
    ts = datetime.utcnow().isoformat()
    prev_hash = _get_last_hash()

    # Serialize event data deterministically
    event_payload = json.dumps({
        "user_id": user_id,
        "event_type": event_type,
        "ts": ts,
        "metadata": metadata,
    }, sort_keys=True)

    event_hash = _hash_event(event_payload, prev_hash)

    entry = {
        "ts": ts,
        "user_id": user_id,
        "event_type": event_type,
        "metadata": metadata,
        "prev_hash": prev_hash,
        "hash": event_hash,
        "notify_counselor": notify_counselor,
    }

    # Append to ledger file (append-only = immutable)
    try:
        with open(LEDGER_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as e:
        print(f"[LEDGER] ⚠️  Could not write to ledger: {e}")

    # Also persist to mock DB
    try:
        from data.db import save_audit_event
        save_audit_event(
            user_id=user_id,
            event_type=event_type,
            event_hash=event_hash,
            metadata=metadata,
        )
    except Exception as e:
        print(f"[LEDGER] DB write error: {e}")

    print(f"[LEDGER] 🔐 {event_type} | Hash: {event_hash[:16]}... | User: {user_id}")

    if notify_counselor:
        _fire_counselor_webhook(entry)

    return entry


def _fire_counselor_webhook(entry: dict):
    """Simulate firing a webhook to the institutional counselor dashboard."""
    print(f"[LEDGER] 📡 Webhook fired to Counselor Dashboard:")
    print(f"         Event   : {entry['event_type']}")
    print(f"         User    : {entry['user_id']}")
    print(f"         Hash    : {entry['hash'][:24]}...")
    print(f"         Time    : {entry['ts']}")


def verify_ledger_integrity() -> dict:
    """
    Verify the entire ledger chain is intact (no tampering).
    Returns: {"valid": bool, "entries": int, "broken_at": str|None}
    """
    if not os.path.exists(LEDGER_PATH):
        return {"valid": True, "entries": 0, "broken_at": None}

    entries = []
    try:
        with open(LEDGER_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
    except Exception as e:
        return {"valid": False, "entries": 0, "broken_at": f"Parse error: {e}"}

    prev_hash = "0" * 64
    for i, entry in enumerate(entries):
        event_payload = json.dumps({
            "user_id": entry["user_id"],
            "event_type": entry["event_type"],
            "ts": entry["ts"],
            "metadata": entry["metadata"],
        }, sort_keys=True)

        expected_hash = _hash_event(event_payload, prev_hash)

        if entry["hash"] != expected_hash:
            return {
                "valid": False,
                "entries": len(entries),
                "broken_at": f"Entry #{i} | ts={entry['ts']}",
            }
        prev_hash = entry["hash"]

    return {"valid": True, "entries": len(entries), "broken_at": None}


def get_recent_events(limit: int = 50) -> list[dict]:
    """Read the last N events from the ledger."""
    if not os.path.exists(LEDGER_PATH):
        return []
    entries = []
    try:
        with open(LEDGER_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
    except Exception:
        pass
    return entries[-limit:]
