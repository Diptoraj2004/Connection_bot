# llm_helper.py
"""
Simple LLM fallback for empathetic responses.
If you configure an LLM later (OpenAI/HuggingFace), replace generate_response().
"""

import random

DEFAULT_EMPATHETIC = [
    "I hear you — that sounds really difficult. I'm here with you.",
    "Thank you for telling me that. It's okay to feel this way.",
    "You're not alone in this. Would you like breathing tips or to connect with a counsellor?",
    "I appreciate your honesty. Do you want some exercises to help right now?"
]

def generate_response(user_text: str) -> str:
    # Lightweight fallback; implement LLM call if configured
    return random.choice(DEFAULT_EMPATHETIC)
