"""
data/questionnaires.py — Complete validated questionnaire bank.
PHQ-9, PHQ-15, GAD-7, GHQ-12, K-10, AQ-10, ASRS, Sleep — all 0-3 scale.
"""
from config import settings

QUESTIONNAIRE_BANK = {
    "phq-9": {
        "name": "PHQ-9 Depression Screening",
        "description": "Over the last 2 weeks, how often have you been bothered by any of the following?",
        "options_global": [
            {"text": "Not at all", "value": 0}, {"text": "Several days", "value": 1},
            {"text": "More than half the days", "value": 2}, {"text": "Nearly every day", "value": 3},
        ],
        "questions": [
            {"id": "phq1", "text": "Little interest or pleasure in doing things"},
            {"id": "phq2", "text": "Feeling down, depressed, or hopeless"},
            {"id": "phq3", "text": "Trouble falling or staying asleep, or sleeping too much"},
            {"id": "phq4", "text": "Feeling tired or having little energy"},
            {"id": "phq5", "text": "Poor appetite or overeating"},
            {"id": "phq6", "text": "Feeling bad about yourself, or that you are a failure"},
            {"id": "phq7", "text": "Trouble concentrating on things"},
            {"id": "phq8", "text": "Moving or speaking so slowly others noticed, or being unusually fidgety/restless"},
            {"id": "phq9", "text": "Thoughts that you would be better off dead, or of hurting yourself"},
        ],
        "max_score": 27,
        "is_crisis_q": "phq9",
    },
    "phq-15": {
        "name": "PHQ-15 Somatic Symptom Screening",
        "description": "Over the last 4 weeks, how much have you been bothered by any of the following physical problems?",
        "options_global": [
            {"text": "Not bothered at all", "value": 0},
            {"text": "Bothered a little",   "value": 1},
            {"text": "Bothered a lot",      "value": 2},
        ],
        "questions": [
            {"id": "s1",  "text": "Stomach pain"},
            {"id": "s2",  "text": "Back pain"},
            {"id": "s3",  "text": "Pain in your arms, legs, or joints (knees, hips, etc.)"},
            {"id": "s4",  "text": "Headaches"},
            {"id": "s5",  "text": "Chest pain"},
            {"id": "s6",  "text": "Dizziness"},
            {"id": "s7",  "text": "Fainting spells"},
            {"id": "s8",  "text": "Feeling your heart pound or race"},
            {"id": "s9",  "text": "Shortness of breath"},
            {"id": "s10", "text": "Constipation, loose bowels, or diarrhoea"},
            {"id": "s11", "text": "Nausea, gas, or indigestion"},
            {"id": "s12", "text": "Feeling tired or having low energy"},
            {"id": "s13", "text": "Trouble sleeping"},
            {"id": "s14", "text": "Feeling your hands or feet going numb or tingling"},
            {"id": "s15", "text": "Feeling hot flushes or cold chills"},
        ],
        "max_score": 30,
        "note": "Catches somatic presentations of mental health issues — common in Indian context.",
    },
    "gad-7": {
        "name": "GAD-7 Anxiety Screening",
        "description": "Over the last 2 weeks, how often have you been bothered by the following?",
        "options_global": [
            {"text": "Not at all", "value": 0}, {"text": "Several days", "value": 1},
            {"text": "More than half the days", "value": 2}, {"text": "Nearly every day", "value": 3},
        ],
        "questions": [
            {"id": "gad1", "text": "Feeling nervous, anxious, or on edge"},
            {"id": "gad2", "text": "Not being able to stop or control worrying"},
            {"id": "gad3", "text": "Worrying too much about different things"},
            {"id": "gad4", "text": "Trouble relaxing"},
            {"id": "gad5", "text": "Being so restless that it is hard to sit still"},
            {"id": "gad6", "text": "Becoming easily annoyed or irritable"},
            {"id": "gad7", "text": "Feeling afraid as if something awful might happen"},
        ],
        "max_score": 21,
    },
    "ghq-12": {
        "name": "GHQ-12 General Mental Health",
        "description": "Compared to your usual, over the last few weeks have you...",
        "options_global": [
            {"text": "Better than usual", "value": 0}, {"text": "Same as usual", "value": 0},
            {"text": "Less than usual", "value": 1},    {"text": "Much less than usual", "value": 1},
        ],
        "questions": [
            {"id": "ghq1",  "text": "Been able to concentrate on whatever you are doing?"},
            {"id": "ghq2",  "text": "Lost much sleep over worry?"},
            {"id": "ghq3",  "text": "Felt that you are playing a useful part in things?"},
            {"id": "ghq4",  "text": "Felt capable of making decisions about things?"},
            {"id": "ghq5",  "text": "Felt constantly under strain?"},
            {"id": "ghq6",  "text": "Felt you couldn't overcome your difficulties?"},
            {"id": "ghq7",  "text": "Been able to enjoy your normal day-to-day activities?"},
            {"id": "ghq8",  "text": "Been able to face up to your problems?"},
            {"id": "ghq9",  "text": "Been feeling unhappy and depressed?"},
            {"id": "ghq10", "text": "Been losing confidence in yourself?"},
            {"id": "ghq11", "text": "Been thinking of yourself as a worthless person?"},
            {"id": "ghq12", "text": "Been feeling reasonably happy, all things considered?"},
        ],
        "max_score": 12,
    },
    "aq10": {
        "name": "AQ-10 Autism Spectrum Screening",
        "description": "Please indicate how strongly you agree or disagree with each statement.",
        "questions": [
            {"id":"aq1",  "text":"I often notice small sounds when others do not.",
             "options":[{"text":"Definitely Agree","value":1},{"text":"Slightly Agree","value":1},{"text":"Slightly Disagree","value":0},{"text":"Definitely Disagree","value":0}]},
            {"id":"aq2",  "text":"I usually concentrate more on the whole picture, rather than small details.",
             "options":[{"text":"Definitely Agree","value":0},{"text":"Slightly Agree","value":0},{"text":"Slightly Disagree","value":1},{"text":"Definitely Disagree","value":1}]},
            {"id":"aq3",  "text":"I find it easy to do more than one thing at once.",
             "options":[{"text":"Definitely Agree","value":0},{"text":"Slightly Agree","value":0},{"text":"Slightly Disagree","value":1},{"text":"Definitely Disagree","value":1}]},
            {"id":"aq4",  "text":"If there is an interruption, I can switch back to what I was doing very quickly.",
             "options":[{"text":"Definitely Agree","value":0},{"text":"Slightly Agree","value":0},{"text":"Slightly Disagree","value":1},{"text":"Definitely Disagree","value":1}]},
            {"id":"aq5",  "text":"I find it easy to read between the lines when someone is talking to me.",
             "options":[{"text":"Definitely Agree","value":0},{"text":"Slightly Agree","value":0},{"text":"Slightly Disagree","value":1},{"text":"Definitely Disagree","value":1}]},
            {"id":"aq6",  "text":"I know how to tell if someone listening to me is getting bored.",
             "options":[{"text":"Definitely Agree","value":0},{"text":"Slightly Agree","value":0},{"text":"Slightly Disagree","value":1},{"text":"Definitely Disagree","value":1}]},
            {"id":"aq7",  "text":"When reading a story I find it difficult to work out the characters intentions.",
             "options":[{"text":"Definitely Agree","value":1},{"text":"Slightly Agree","value":1},{"text":"Slightly Disagree","value":0},{"text":"Definitely Disagree","value":0}]},
            {"id":"aq8",  "text":"I like to collect information about categories of things.",
             "options":[{"text":"Definitely Agree","value":1},{"text":"Slightly Agree","value":1},{"text":"Slightly Disagree","value":0},{"text":"Definitely Disagree","value":0}]},
            {"id":"aq9",  "text":"I find it easy to work out what someone is thinking just by looking at their face.",
             "options":[{"text":"Definitely Agree","value":0},{"text":"Slightly Agree","value":0},{"text":"Slightly Disagree","value":1},{"text":"Definitely Disagree","value":1}]},
            {"id":"aq10", "text":"I find it difficult to work out peoples intentions.",
             "options":[{"text":"Definitely Agree","value":1},{"text":"Slightly Agree","value":1},{"text":"Slightly Disagree","value":0},{"text":"Definitely Disagree","value":0}]},
        ],
        "max_score": 10,
    },
    "asrs": {
        "name": "ASRS v1.1 ADHD Screening",
        "description": "Over the past 6 months, how often have you had trouble with the following?",
        "options_global": [
            {"text": "Never", "value": 0}, {"text": "Rarely", "value": 1},
            {"text": "Sometimes", "value": 2}, {"text": "Often", "value": 3},
        ],
        "questions": [
            {"id":"asrs1","text":"How often do you have trouble wrapping up the final details of a project?"},
            {"id":"asrs2","text":"How often do you have difficulty getting things in order for a task requiring organisation?"},
            {"id":"asrs3","text":"How often do you have problems remembering appointments or obligations?"},
            {"id":"asrs4","text":"When a task requires a lot of thought, how often do you avoid or delay getting started?"},
            {"id":"asrs5","text":"How often do you fidget or squirm when you have to sit for a long time?"},
            {"id":"asrs6","text":"How often do you feel overly active and compelled to do things, like driven by a motor?"},
        ],
        "max_score": 18,
    },
    "k-10": {
        "name": "K-10 Psychological Distress Scale",
        "description": "In the past 30 days, how often did you feel...",
        "options_global": [
            {"text": "None of the time", "value": 0},     {"text": "A little of the time", "value": 1},
            {"text": "Some of the time", "value": 2},     {"text": "Most of the time", "value": 3},
        ],
        "questions": [
            {"id":"k1", "text":"Tired out for no good reason?"},
            {"id":"k2", "text":"Nervous?"},
            {"id":"k3", "text":"So nervous that nothing could calm you down?"},
            {"id":"k4", "text":"Hopeless?"},
            {"id":"k5", "text":"Restless or fidgety?"},
            {"id":"k6", "text":"So restless you could not sit still?"},
            {"id":"k7", "text":"Depressed?"},
            {"id":"k8", "text":"That everything was an effort?"},
            {"id":"k9", "text":"So sad that nothing could cheer you up?"},
            {"id":"k10","text":"Worthless?"},
        ],
        "max_score": 30,
    },
    "sleep": {
        "name": "Sleep Quality Screening",
        "description": "Over the past month...",
        "questions": [
            {"id":"sl1","text":"How would you rate your overall sleep quality?",
             "options":[{"text":"Very good","value":0},{"text":"Fairly good","value":1},{"text":"Fairly bad","value":2},{"text":"Very bad","value":3}]},
            {"id":"sl2","text":"How many hours of actual sleep did you get on average?",
             "options":[{"text":"More than 7 hours","value":0},{"text":"6-7 hours","value":1},{"text":"5-6 hours","value":2},{"text":"Less than 5 hours","value":3}]},
            {"id":"sl3","text":"How often did you wake up in the middle of the night?",
             "options":[{"text":"Not during past month","value":0},{"text":"Less than once a week","value":1},{"text":"Once or twice a week","value":2},{"text":"Three or more times a week","value":3}]},
            {"id":"sl4","text":"How often have you had trouble staying awake during the day?",
             "options":[{"text":"Not during past month","value":0},{"text":"Less than once a week","value":1},{"text":"Once or twice a week","value":2},{"text":"Three or more times a week","value":3}]},
        ],
        "max_score": 12,
    },
}

def score_responses(test_name: str, answers: list) -> dict:
    test_name = test_name.lower()
    q_data = QUESTIONNAIRE_BANK.get(test_name)
    if not q_data:
        return {"error": f"Unknown test: {test_name}"}
    raw_score = sum(answers)
    thresh = settings.escalation_thresholds.get(test_name, {})
    crisis_flag = False
    severity = "minimal"; escalate = False; interpretation = ""; recommended_resources = []
    if test_name in ("phq-9", "phq-15"):
        if test_name == "phq-9" and len(answers) >= 9 and answers[8] >= 1:
            crisis_flag = True
        if raw_score >= 20: severity, escalate = "severe", True; interpretation = "Severe symptoms. Immediate professional support recommended."; recommended_resources = ["book_counselor","crisis_line","video_depression"]
        elif raw_score >= 15: severity, escalate = "moderately_severe", True; interpretation = "Moderately severe. Professional support recommended."; recommended_resources = ["book_counselor","video_depression","audio_breathing"]
        elif raw_score >= 10: severity = "moderate"; interpretation = "Moderate. Consider speaking to a counselor."; recommended_resources = ["peer_support","video_depression","lofi_music"]
        elif raw_score >= 5:  severity = "mild"; interpretation = "Mild symptoms. Self-care suggested."; recommended_resources = ["lofi_music","peer_support"]
        else: severity = "minimal"; interpretation = "Minimal or no symptoms detected."
    elif test_name == "gad-7":
        if raw_score >= 15: severity, escalate = "severe", True; interpretation = "Severe anxiety."; recommended_resources = ["book_counselor","audio_breathing","crisis_line"]
        elif raw_score >= 10: severity = "moderate"; interpretation = "Moderate anxiety."; recommended_resources = ["audio_breathing","peer_support"]
        elif raw_score >= 5: severity = "mild"; interpretation = "Mild anxiety."; recommended_resources = ["audio_breathing","lofi_music"]
        else: severity = "minimal"; interpretation = "Minimal anxiety."
    elif test_name == "ghq-12":
        if raw_score >= 4: severity, escalate = "significant", True; interpretation = "Significant distress detected."; recommended_resources = ["book_counselor","peer_support"]
        else: severity = "normal"; interpretation = "General mental health within normal range."
    elif test_name == "aq10":
        if raw_score >= thresh.get("refer", 6): severity, escalate = "refer", True; interpretation = "Possible autism spectrum traits. Formal assessment recommended."; recommended_resources = ["specialist_autism","book_counselor"]
        else: severity = "typical"; interpretation = "Score within typical range."
    elif test_name == "asrs":
        if raw_score >= thresh.get("refer", 4): severity, escalate = "refer", True; interpretation = "ADHD traits detected. Formal evaluation recommended."; recommended_resources = ["specialist_adhd","focus_music","book_counselor"]
        else: severity = "typical"; interpretation = "Score within typical range."
    elif test_name == "k-10":
        if raw_score >= thresh.get("severe", 20): severity, escalate = "severe", True; interpretation = "Severe psychological distress."; recommended_resources = ["book_counselor","crisis_line"]
        elif raw_score >= thresh.get("moderate", 14): severity = "moderate"; interpretation = "Moderate distress."; recommended_resources = ["peer_support","lofi_music"]
        else: severity = "low"; interpretation = "Low distress levels."
    elif test_name == "sleep":
        if raw_score >= 7: severity = "poor"; interpretation = "Poor sleep quality."; recommended_resources = ["audio_sleep","lofi_music"]
        elif raw_score >= 4: severity = "fair"; interpretation = "Fair sleep quality."
        else: severity = "good"; interpretation = "Sleep quality appears good."
    return {"test": test_name, "score": raw_score, "max_score": q_data.get("max_score", 0),
            "severity": severity, "escalate": escalate or crisis_flag, "crisis_flag": crisis_flag,
            "interpretation": interpretation, "recommended_resources": recommended_resources}

def get_questionnaire(test_name: str): return QUESTIONNAIRE_BANK.get(test_name.lower())
def list_questionnaires(): return list(QUESTIONNAIRE_BANK.keys())
def infer_test_from_text(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ["autism","sensory","overwhelm","spectrum","asperger"]): return "aq10"
    if any(w in t for w in ["adhd","focus","distracted","attention","hyperactive"]): return "asrs"
    if any(w in t for w in ["anxious","anxiety","panic","worry","scared","dread"]): return "gad-7"
    if any(w in t for w in ["sleep","insomnia","can't sleep","tired all the time"]): return "sleep"
    if any(w in t for w in ["stomach","headache","body pain","chest pain","physical"]): return "phq-15"
    if any(w in t for w in ["distress","overwhelmed","can't cope","stressed"]): return "k-10"
    return "phq-9"
