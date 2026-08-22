"""
services/music_ai.py — AI-Powered Mood-Based Music Recommendation Engine.
"""
from config import settings

MOOD_MUSIC_MAP = {
    "anxious": [
        {"title": "Weightless", "artist": "Marconi Union", "type": "ambient", "why": "Clinically shown to reduce anxiety by 65%"},
        {"title": "Raga Bhairavi", "artist": "Pandit Hariprasad Chaurasia", "type": "classical_indian", "why": "Traditional morning raga for calm"},
        {"title": "4-4-4 Box Breathing Guide", "artist": "SentinelMind", "type": "audio_guide", "url": "/media/box-breathing"},
    ],
    "depressed": [
        {"title": "Iktara", "artist": "Lucky Ali", "type": "bollywood", "why": "Gentle and introspective — meets you where you are"},
        {"title": "The Night Will Always Win", "artist": "Manchester Orchestra", "type": "indie", "why": "Validates the feeling without staying there"},
        {"title": "Behavioral Activation Guide", "artist": "SentinelMind", "type": "video", "url": "/media/behavioral-activation"},
    ],
    "sad": [
        {"title": "Channa Mereya", "artist": "Arijit Singh", "type": "bollywood", "why": "Emotional release — cathartic listening"},
        {"title": "Fix You", "artist": "Coldplay", "type": "pop", "why": "Moves from grief toward hope"},
        {"title": "Lo-Fi Study Beats", "artist": "Various", "type": "lofi", "url": "/media/lofi"},
    ],
    "adhd": [
        {"title": "40Hz Binaural Focus Beats", "artist": "Brain.fm", "type": "binaural", "why": "Gamma waves (40Hz) improve executive function"},
        {"title": "Beethoven Symphony No. 5", "artist": "Berlin Philharmonic", "type": "classical", "why": "Structured complexity aids focus"},
        {"title": "Focus Mode Guide", "artist": "SentinelMind", "type": "audio_guide", "url": "/media/focus-guide"},
    ],
    "angry": [
        {"title": "Breathe (2 AM)", "artist": "Anna Nalick", "type": "pop", "why": "Reframes frustration into release"},
        {"title": "Raga Yaman", "artist": "Ustad Rashid Khan", "type": "classical_indian", "why": "Evening raga for emotional regulation"},
        {"title": "Progressive Muscle Relaxation", "artist": "SentinelMind", "type": "audio_guide", "url": "/media/pmr"},
    ],
    "stressed": [
        {"title": "Clair de Lune", "artist": "Debussy", "type": "classical", "why": "Parasympathetic nervous system activation"},
        {"title": "Tum Hi Ho", "artist": "Arijit Singh", "type": "bollywood", "why": "Familiar comfort reduces cortisol"},
        {"title": "5-4-3-2-1 Grounding Guide", "artist": "SentinelMind", "type": "audio_guide", "url": "/media/grounding"},
    ],
    "neutral": [
        {"title": "Lo-Fi Hip Hop Radio", "artist": "Various", "type": "lofi", "url": "/media/lofi"},
        {"title": "Nuvole Bianche", "artist": "Ludovico Einaudi", "type": "contemporary_classical", "why": "Contemplative and centering"},
    ],
    "happy": [
        {"title": "Badtameez Dil", "artist": "Pritam", "type": "bollywood", "why": "Amplify the good energy"},
        {"title": "Happy", "artist": "Pharrell Williams", "type": "pop", "why": "Reinforce positive affect"},
    ],
    "sleep": [
        {"title": "Delta Wave Sleep Music", "artist": "SentinelMind", "type": "sleep_aid", "url": "/media/delta-sleep"},
        {"title": "Raga Sohni", "artist": "Pandit Shivkumar Sharma", "type": "classical_indian", "why": "Night raga traditionally used for rest"},
    ],
}


def get_mood_resources(mood: str, limit: int = 3) -> str:
    """Return formatted resource list for a given mood."""
    mood_key = mood.lower()
    resources = MOOD_MUSIC_MAP.get(mood_key, MOOD_MUSIC_MAP["neutral"])[:limit]
    lines = ["🎵 **Recommended Resources for You:**\n"]
    for r in resources:
        icon = {"audio_guide": "🎙️", "video": "📹", "lofi": "🎧",
                "binaural": "🧠", "classical_indian": "🪘"}.get(r["type"], "🎵")
        why_note = f" — *{r['why']}*" if r.get("why") else ""
        lines.append(f"{icon} **{r['title']}** by {r['artist']}{why_note}")
    return "\n".join(lines)


def get_resources_json(mood: str) -> list[dict]:
    mood_key = mood.lower()
    return MOOD_MUSIC_MAP.get(mood_key, MOOD_MUSIC_MAP["neutral"])
