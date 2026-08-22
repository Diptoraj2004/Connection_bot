"""
core/scoring.py — Re-exports scoring utilities from data/questionnaires.py.

Exists so any code that does `from core.scoring import score_responses`
still works. The canonical implementation lives in data/questionnaires.py.
"""
from data.questionnaires import score_responses, infer_test_from_text, get_questionnaire

__all__ = ["score_responses", "infer_test_from_text", "get_questionnaire"]
