"""
core/pii_scrubber.py — Microsoft Presidio PII sanitization layer.

Wraps Presidio with a simple scrub() interface.
All user text passes through this before hitting the AI/LLM layer.
"""
import re
from functools import lru_cache

_analyzer   = None
_anonymizer = None
_initialized = False


def _init():
    global _analyzer, _anonymizer, _initialized
    if _initialized:
        return
    try:
        from presidio_analyzer import AnalyzerEngine
        from presidio_anonymizer import AnonymizerEngine
        _analyzer   = AnalyzerEngine()
        _anonymizer = AnonymizerEngine()
        _initialized = True
        print("[PII] ✅ Presidio initialized")
    except ImportError:
        print("[PII] ⚠️  presidio not installed — using regex-only scrubber")
        _initialized = True  # Mark as done so we don't retry every call


_REGEX_PATTERNS = [
    # Indian mobile numbers
    (re.compile(r"\b[6-9]\d{9}\b"), "[PHONE]"),
    # Email addresses
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[a-z]{2,}\b", re.I), "[EMAIL]"),
    # Aadhar card (12 digits)
    (re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b"), "[AADHAR]"),
    # Any 10-digit number that looks like a phone
    (re.compile(r"\b\d{10}\b"), "[PHONE]"),
]


def scrub(text: str) -> str:
    """
    Remove all PII from text using Presidio + regex fallback.
    Returns sanitized text safe for AI processing.
    """
    if not text or not text.strip():
        return text

    _init()

    # ── Step 1: Presidio (if available) ───────────────────────────────────────
    if _analyzer and _anonymizer:
        try:
            results = _analyzer.analyze(
                text=text,
                entities=["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "LOCATION",
                          "CREDIT_CARD", "DATE_TIME", "NRP"],
                language="en",
            )
            if results:
                text = _anonymizer.anonymize(text=text, analyzer_results=results).text
        except Exception as e:
            print(f"[PII] Presidio error (falling back to regex): {e}")

    # ── Step 2: Regex patterns (catch Indian-specific formats Presidio misses) ─
    for pattern, replacement in _REGEX_PATTERNS:
        text = pattern.sub(replacement, text)

    return text.strip()


def scrub_dict(data: dict, keys: list[str]) -> dict:
    """Scrub specific keys in a dictionary."""
    cleaned = dict(data)
    for key in keys:
        if key in cleaned and isinstance(cleaned[key], str):
            cleaned[key] = scrub(cleaned[key])
    return cleaned
