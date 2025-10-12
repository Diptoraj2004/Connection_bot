# Patched: 2025-09-14 - production-ready
"""
Questionnaire loader and canonical question banks.
Loads question banks from datasets/question_banks/*.json if present,
otherwise falls back to small embedded banks for core instruments.
"""

import json
import os
from typing import Dict, List, Any, Optional

BASE_DIR = os.path.dirname(__file__)
QUESTION_BANKS_DIR = os.path.join(BASE_DIR, "datasets", "question_banks")

def _load_json_file(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)

def list_available_questionnaires() -> List[str]:
    """Return list of questionnaire names available in question_banks dir."""
    if not os.path.isdir(QUESTION_BANKS_DIR):
        return []
    files = [f[:-5] for f in os.listdir(QUESTION_BANKS_DIR) if f.endswith(".json")]
    return files

def get_questionnaire(name: str, locale: str = "en") -> Dict[str, Any]:
    """
    Return canonical questionnaire structure:
    {
       "id": "phq9",
       "title": "PHQ-9",
       "version": "1.0",
       "questions": [
           {"id": "phq9_q1", "text": "...", "options":[{"text": "Not at all", "value": 0}, ...]},
           ...
       ],
       "thresholds": {"moderate": 10, "severe": 20} (optional)
    }
    """
    # try filesystem first
    fname = os.path.join(QUESTION_BANKS_DIR, f"{name.lower()}.json")
    if os.path.exists(fname):
        data = _load_json_file(fname)
        # support locale selection in future
        return data

    # Fallback built-in small canonical banks for core instruments (stage 1)
    name_lower = name.lower()
    if name_lower in ("phq9", "phq-9"):
        return _phq9()
    if name_lower in ("gad7", "gad-7"):
        return _gad7()
    if name_lower in ("ghq12", "ghq-12"):
        return _ghq12()
    if name_lower in ("who5", "who-5"):
        return _who5()
    if name_lower in ("k6", "kessler6"):
        return _k6()
    if name_lower in ("dass21", "dass-21"):
        return _dass21()
    if name_lower in ("student_sleep", "student_sleep_index", "sleep"):
        return _student_sleep()
    if name_lower in ("ucla", "ucla_loneliness"):
        return _ucla()
    # Add more fallbacks as needed
    raise ValueError(f"Questionnaire '{name}' not found in question banks or embedded fallbacks.")

# --------------------
# Small built-in canonical sets (concise; full texts can be placed in datasets/question_banks/*.json)
# --------------------
def _phq9():
    q = [
        "Little interest or pleasure in doing things",
        "Feeling down, depressed, or hopeless",
        "Trouble falling or staying asleep, or sleeping too much",
        "Feeling tired or having little energy",
        "Poor appetite or overeating",
        "Feeling bad about yourself — or that you are a failure or have let yourself or your family down",
        "Trouble concentrating on things, such as reading the newspaper or watching television",
        "Moving or speaking so slowly that other people could have noticed. Or the opposite — being so fidgety or restless that you have been moving around a lot more than usual",
        "Thoughts that you would be better off dead or of hurting yourself in some way"
    ]
    questions = []
    for i, text in enumerate(q, start=1):
        questions.append({
            "id": f"phq9_q{i}",
            "text": text,
            "options": [
                {"text": "Not at all", "value": 0},
                {"text": "Several days", "value": 1},
                {"text": "More than half the days", "value": 2},
                {"text": "Nearly every day", "value": 3},
            ]
        })
    return {
        "id": "phq-9",
        "title": "PHQ-9",
        "version": "1.0",
        "questions": questions,
        "thresholds": {"moderate": 10, "moderately_severe": 15, "severe": 20}
    }

def _gad7():
    q = [
        "Feeling nervous, anxious, or on edge",
        "Not being able to stop or control worrying",
        "Worrying too much about different things",
        "Trouble relaxing",
        "Being so restless that it's hard to sit still",
        "Becoming easily annoyed or irritable",
        "Feeling afraid as if something awful might happen"
    ]
    questions = []
    for i, text in enumerate(q, start=1):
        questions.append({
            "id": f"gad7_q{i}",
            "text": text,
            "options": [
                {"text": "Not at all", "value": 0},
                {"text": "Several days", "value": 1},
                {"text": "More than half the days", "value": 2},
                {"text": "Nearly every day", "value": 3},
            ]
        })
    return {
        "id": "gad-7",
        "title": "GAD-7",
        "version": "1.0",
        "questions": questions,
        "thresholds": {"moderate": 10, "severe": 15}
    }

def _ghq12():
    # GHQ-12 uses different response scales; simplified mapping here
    texts = [
        "Been able to concentrate on what you're doing?",
        "Lost much sleep over worry?",
        "Felt that you are playing a useful part in things?",
        "Felt capable of making decisions about things?",
        "Felt constantly under strain?",
        "Felt you couldn't overcome your difficulties?",
        "Been able to enjoy your normal day-to-day activities?",
        "Been able to face up to your problems?",
        "Been feeling unhappy and depressed?",
        "Been losing confidence in yourself?",
        "Been thinking of yourself as a worthless person?",
        "Been feeling reasonably happy, all things considered?"
    ]
    questions = []
    for i, text in enumerate(texts, start=1):
        questions.append({
            "id": f"ghq12_q{i}",
            "text": text,
            "options": [
                {"text": "Better than usual", "value": 0},
                {"text": "Same as usual", "value": 0},
                {"text": "Less than usual", "value": 1},
                {"text": "Much less than usual", "value": 1},
            ]
        })
    return {
        "id": "ghq-12",
        "title": "GHQ-12",
        "version": "1.0",
        "questions": questions,
        "thresholds": {"possible_case": 4}
    }

def _who5():
    questions = []
    texts = [
        "I have felt cheerful and in good spirits",
        "I have felt calm and relaxed",
        "I have felt active and vigorous",
        "I woke up feeling fresh and rested",
        "My daily life has been filled with things that interest me"
    ]
    for i, text in enumerate(texts, start=1):
        questions.append({
            "id": f"who5_q{i}",
            "text": text,
            "options": [
                {"text": "At no time", "value": 0},
                {"text": "Some of the time", "value": 1},
                {"text": "Less than half of the time", "value": 2},
                {"text": "More than half of the time", "value": 3},
                {"text": "Most of the time", "value": 4},
                {"text": "All of the time", "value": 5},
            ]
        })
    return {"id": "who-5", "title": "WHO-5", "version": "1.0", "questions": questions}

def _k6():
    texts = [
        "During the past 30 days, how often did you feel nervous?",
        "… so nervous that nothing could calm you down?",
        "… hopeless?",
        "… restless or fidgety?",
        "… so depressed that nothing could cheer you up?",
        "… that everything was an effort?",
        "… worthless?"
    ]
    questions = []
    for i, text in enumerate(texts[:6], start=1):
        questions.append({
            "id": f"k6_q{i}",
            "text": text,
            "options": [
                {"text": "None of the time", "value": 0},
                {"text": "A little of the time", "value": 1},
                {"text": "Some of the time", "value": 2},
                {"text": "Most of the time", "value": 3},
                {"text": "All of the time", "value": 4},
            ]
        })
    return {"id": "k6", "title": "K6", "version": "1.0", "questions": questions}

def _dass21():
    # DASS-21 is longer; provide placeholder subset here and expect full file in datasets folder
    texts = [
        "I found it hard to wind down",
        "I was aware of dryness of my mouth",
        "I couldn't seem to experience any positive feeling at all",
        "I experienced breathing difficulty (e.g., excessively rapid breathing, breathlessness in the absence of physical exertion)",
        "I found it difficult to work up the initiative to do things"
    ]
    questions = []
    for i, text in enumerate(texts, start=1):
        questions.append({
            "id": f"dass21_q{i}",
            "text": text,
            "options": [
                {"text": "Did not apply to me at all", "value": 0},
                {"text": "Applied to me to some degree, or some of the time", "value": 1},
                {"text": "Applied to me to a considerable degree, or a good part of the time", "value": 2},
                {"text": "Applied to me very much, or most of the time", "value": 3},
            ]
        })
    return {"id": "dass-21", "title": "DASS-21", "version": "1.0", "questions": questions}

def _student_sleep():
    # simplified sleep question set
    questions = [
        {"id": "sleep_q1", "text": "On average how many hours do you sleep each night?", "options": [
            {"text": "<4 hours", "value": 0},
            {"text": "4-6 hours", "value": 1},
            {"text": "6-8 hours", "value": 2},
            {"text": ">8 hours", "value": 3}
        ]},
        {"id": "sleep_q2", "text": "Do you have trouble staying asleep?", "options": [
            {"text": "Never", "value": 0},
            {"text": "Sometimes", "value": 1},
            {"text": "Often", "value": 2},
            {"text": "Almost always", "value": 3}
        ]}
    ]
    return {"id": "student_sleep", "title": "Student Sleep Index", "version": "1.0", "questions": questions}

def _ucla():
    texts = [
        "I feel in tune with the people around me",
        "I lack companionship",
        "There is no one I can turn to",
        "I do not feel close to people"
    ]
    questions = []
    for i, text in enumerate(texts, start=1):
        questions.append({
            "id": f"ucla_q{i}",
            "text": text,
            "options": [
                {"text": "Never", "value": 0},
                {"text": "Rarely", "value": 1},
                {"text": "Sometimes", "value": 2},
                {"text": "Often", "value": 3},
            ]
        })
    return {"id": "ucla", "title": "UCLA Loneliness Scale (short)", "version": "1.0", "questions": questions}
