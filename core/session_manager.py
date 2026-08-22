"""
core/session_manager.py — In-memory session registry with TTL cleanup.
"""
import threading
from datetime import datetime, timedelta
from typing import Optional
from config import settings


_sessions: dict = {}
_lock = threading.Lock()


def get_or_create(user_id: str):
    """Get existing session or create a new one."""
    from core.chat_session import ChatSession
    with _lock:
        _cleanup_expired()
        if user_id not in _sessions:
            _sessions[user_id] = ChatSession(user_id=user_id)
            print(f"[SESSION] Created new session for {user_id}")
        return _sessions[user_id]


def get(user_id: str) -> Optional[object]:
    with _lock:
        return _sessions.get(user_id)


def destroy(user_id: str):
    with _lock:
        _sessions.pop(user_id, None)


def reset(user_id: str):
    """Reset session (start fresh conversation)."""
    from core.chat_session import ChatSession
    with _lock:
        _sessions[user_id] = ChatSession(user_id=user_id)
    return _sessions[user_id]


def active_count() -> int:
    return len(_sessions)


def _cleanup_expired():
    """Remove sessions inactive longer than SESSION_TTL_MINUTES."""
    ttl = timedelta(minutes=settings.session_ttl_minutes)
    now = datetime.utcnow()
    expired = []
    for uid, session in _sessions.items():
        try:
            last = datetime.fromisoformat(session.last_active)
            if now - last > ttl:
                expired.append(uid)
        except Exception:
            pass
    for uid in expired:
        del _sessions[uid]
        print(f"[SESSION] Expired session for {uid}")

def start_cleanup_thread(interval_minutes: int = 30):
    """
    Start a background thread that cleans expired sessions every N minutes.
    Call this from main.py lifespan startup so TTL runs even when no new
    sessions are created (prevents unbounded dict growth when system is idle).
    """
    import threading
    def _run():
        import time
        while True:
            time.sleep(interval_minutes * 60)
            with _lock:
                _cleanup_expired()
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    print(f"[SESSION] Background cleanup thread started (every {interval_minutes} min)")
