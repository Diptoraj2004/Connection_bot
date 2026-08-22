"""
services/voice_service.py — Voice-to-Text for Logbook Entries.

Uses OpenAI's Whisper model running LOCALLY — no API key needed.
Supports: mp3, mp4, wav, m4a, ogg, webm (anything ffmpeg handles).

Why Whisper:
  - Runs offline in Colab on CPU (base model ~1GB)
  - Supports Hindi, Tamil, Telugu, Bengali, Marathi natively
  - Detects language automatically — students can speak in any Indian language
  - Free forever, no per-request cost

Workflow:
  1. Frontend records audio and sends base64-encoded bytes to /api/logbook/voice
  2. This service saves temp file, runs Whisper, returns transcript
  3. Transcript goes through PII scrubber before storage
"""

import os
import base64
import tempfile
from pathlib import Path
from config import settings

_whisper_model = None


def _load_model():
    """Lazy-load Whisper model on first use."""
    global _whisper_model
    if _whisper_model:
        return _whisper_model
    try:
        import whisper
        print(f"[VOICE] Loading Whisper '{settings.whisper_model}' model...")
        _whisper_model = whisper.load_model(settings.whisper_model)
        print("[VOICE] ✅ Whisper ready")
        return _whisper_model
    except ImportError:
        raise RuntimeError(
            "Whisper not installed. Run: pip install openai-whisper"
        )


def transcribe_audio_file(file_path: str) -> dict:
    """
    Transcribe an audio file to text.
    Returns: {transcript, language, confidence, duration_seconds}
    """
    model = _load_model()

    result = model.transcribe(
        file_path,
        task="transcribe",
        verbose=False,
        fp16=False,  # CPU-safe
    )

    transcript = result.get("text", "").strip()
    language   = result.get("language", "unknown")
    segments   = result.get("segments", [])
    duration   = segments[-1]["end"] if segments else 0.0

    # Average log probability as a rough confidence proxy
    avg_logprob = sum(s.get("avg_logprob", -1) for s in segments) / max(len(segments), 1)
    confidence  = min(max(round((avg_logprob + 1.0), 2), 0.0), 1.0)

    return {
        "transcript": transcript,
        "language":   language,
        "confidence": confidence,
        "duration_seconds": round(duration, 1),
        "word_count": len(transcript.split()),
    }


def transcribe_base64(audio_b64: str, extension: str = "webm") -> dict:
    """
    Accept a base64-encoded audio string (from browser MediaRecorder),
    save to temp file, transcribe, clean up.
    """
    audio_bytes = base64.b64decode(audio_b64)

    with tempfile.NamedTemporaryFile(suffix=f".{extension}", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        result = transcribe_audio_file(tmp_path)
    finally:
        os.unlink(tmp_path)

    return result


def transcribe_upload(file_bytes: bytes, filename: str) -> dict:
    """
    Accept raw bytes from a FastAPI UploadFile.
    """
    ext = Path(filename).suffix.lstrip(".") or "wav"
    with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name
    try:
        return transcribe_audio_file(tmp_path)
    finally:
        os.unlink(tmp_path)


def is_whisper_available() -> bool:
    try:
        import whisper
        return True
    except ImportError:
        return False
