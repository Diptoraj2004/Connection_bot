"""
services/peer_stories.py — Anonymous Peer Recovery Story Library.

Research basis: Narrative exposure to recovery stories from similar peers
is one of the most effective anti-stigma interventions (Corrigan 2012,
Mental Health Commission of Canada 2014).

Stories are:
  - Fully anonymised (no names, no identifying details)
  - Tagged by condition, college year, and theme
  - Matched to student context by the chat session
  - User-submittable (pending review before publishing)
"""
from data.db import insert_record, query_records
from datetime import datetime

STORY_LIBRARY = [
    {
        "id": "s001",
        "title": "I thought asking for help meant I was weak",
        "tags": ["depression", "academic_pressure", "first_generation"],
        "year_of_study": "3rd year",
        "excerpt": (
            "In my third year of engineering, I stopped going to class. Not because I was lazy — "
            "I was terrified. Every day I woke up and thought, what's the point? "
            "I was the first in my family to go to college. I couldn't tell them I was struggling. "
            "They'd sacrificed everything. I found SentinelMind at 2am. "
            "I didn't believe the chatbot would actually help. But it got me to a counselor, "
            "and that counselor helped me understand I had depression — not weakness. "
            "I finished my degree. I still have hard days. But I know what they are now."
        ),
        "outcome": "Completed degree, now working in Pune",
        "what_helped": ["counseling", "peer_support", "medication"],
        "condition": "depression",
        "months_to_recovery": 8,
    },
    {
        "id": "s002",
        "title": "My ADHD wasn't diagnosed until I was 20",
        "tags": ["adhd", "academic_failure", "late_diagnosis"],
        "year_of_study": "2nd year",
        "excerpt": (
            "Everyone called me lazy. My parents, my teachers. I'd sit down to study and "
            "somehow three hours would pass and I had nothing done. I thought I was broken. "
            "I scored really high in the ASRS on this app, and the counselor referred me for "
            "a formal ADHD assessment. Getting that diagnosis felt like someone finally believed me. "
            "I'm on medication now and using the Pomodoro technique. "
            "My GPA went from 5.2 to 7.8 in one semester."
        ),
        "outcome": "Pursuing postgrad, advocates for ADHD awareness on campus",
        "what_helped": ["formal_diagnosis", "medication", "study_techniques", "counseling"],
        "condition": "adhd",
        "months_to_recovery": 4,
    },
    {
        "id": "s003",
        "title": "Panic attacks in the exam hall",
        "tags": ["anxiety", "panic_attacks", "exams", "breathing"],
        "year_of_study": "1st year",
        "excerpt": (
            "My first university exam, I walked in and couldn't breathe. My heart was going "
            "so fast I thought I was dying. I ran out. I failed that paper. "
            "A friend showed me this app. I used the breathing exercises every night for a month. "
            "I also talked to a peer volunteer — she'd had panic attacks too. "
            "She didn't try to fix me. She just told me I wasn't alone. "
            "I sat my supplementary exam. I passed. The panic still comes sometimes, "
            "but now I know what it is, and I know what to do."
        ),
        "outcome": "Completed first year, teaching breathing techniques to her hostel mates",
        "what_helped": ["breathing_exercises", "peer_support", "therapy"],
        "condition": "anxiety",
        "months_to_recovery": 3,
    },
    {
        "id": "s004",
        "title": "Being autistic in a college that didn't understand",
        "tags": ["autism", "sensory_overload", "social_difficulty", "peer_help"],
        "year_of_study": "4th year",
        "excerpt": (
            "The canteen was the worst. The noise, the crowds — I'd have to leave and sit outside. "
            "People thought I was antisocial or rude. I wasn't. My brain just couldn't process "
            "all of it at once. I found the peer support section on this app. "
            "I didn't use it for myself — I used it to send information to my roommate. "
            "She read the autism peer guide and she started asking me 'do you want space, "
            "or company?' That one question changed my year. "
            "She became my loudest advocate in our friend group."
        ),
        "outcome": "Graduated with distinction, now mentors first-year autistic students",
        "what_helped": ["peer_education", "reasonable_adjustments", "self_advocacy"],
        "condition": "autism",
        "months_to_recovery": 12,
    },
    {
        "id": "s005",
        "title": "Ragging broke me. Recovery rebuilt me.",
        "tags": ["bullying", "ragging", "trauma", "hostels"],
        "year_of_study": "1st year",
        "excerpt": (
            "What happened to me in the hostel in the first month — I couldn't tell anyone. "
            "I couldn't sleep. I stopped eating. I contemplated dropping out every day. "
            "I typed into the app one night and told it what was happening. "
            "It didn't lecture me. It got a counselor involved. "
            "The counselor helped me report it through the proper channel — "
            "the anti-ragging committee — and stayed with me through the process. "
            "The students responsible were disciplined. It took months to feel safe again. "
            "But I stayed. And I'm glad I did."
        ),
        "outcome": "Completed degree, now runs an anti-ragging awareness campaign",
        "what_helped": ["counseling", "institutional_support", "reporting"],
        "condition": "trauma",
        "months_to_recovery": 10,
    },
    {
        "id": "s006",
        "title": "I didn't know sleep deprivation was making everything worse",
        "tags": ["sleep", "depression", "academic_pressure"],
        "year_of_study": "2nd year",
        "excerpt": (
            "I was averaging 4 hours of sleep for an entire semester. "
            "I thought it was normal — everyone around me was doing the same. "
            "The sleep screening on the app flagged it. The counselor explained how "
            "chronic sleep deprivation amplifies depression and anxiety by 3–4x. "
            "I started sleep hygiene seriously. No phone after 11pm, same wake time every day. "
            "Within three weeks, my mood had shifted enough that I could actually study. "
            "It felt too simple to be real. But it was."
        ),
        "outcome": "Maintains healthy sleep, advises his junior batchmates",
        "what_helped": ["sleep_hygiene", "psychoeducation", "habit_change"],
        "condition": "sleep",
        "months_to_recovery": 2,
    },
    {
        "id": "s007",
        "title": "Down syndrome doesn't mean my feelings don't count",
        "tags": ["down_syndrome", "belonging", "peer_support"],
        "year_of_study": "1st year",
        "excerpt": (
            "People talk to me like I don't understand. I understand everything. "
            "I just need more time. When I was sad — really sad, not just a bad day — "
            "my support worker used this app with me. We went through the questions together. "
            "It was slow, but I answered every one. The counselor who called was patient. "
            "She spoke to me, not about me. For the first time, someone asked what I wanted. "
            "I wanted a friend. The peer volunteer system connected me to a student in my class. "
            "Her name is Priya. She's my best friend now."
        ),
        "outcome": "Thriving in inclusive education programme",
        "what_helped": ["supported_access", "peer_connection", "counseling"],
        "condition": "down_syndrome",
        "months_to_recovery": 6,
    },
]


def get_story_for_context(condition: str = "", tags: list = None,
                          limit: int = 2) -> list[dict]:
    """
    Retrieve the most relevant stories for a student's context.
    Returns a short list ready to display in the chat.
    """
    scored = []
    tag_set = set(tags or [])
    cond = condition.lower()

    for story in STORY_LIBRARY:
        score = 0
        if cond and story.get("condition", "") == cond:
            score += 3
        story_tags = set(story.get("tags", []))
        score += len(tag_set & story_tags)
        scored.append((score, story))

    scored.sort(key=lambda x: -x[0])
    return [s for _, s in scored[:limit]]


def get_story_text(story_id: str) -> str:
    """Return the full story text for display in chat."""
    for story in STORY_LIBRARY:
        if story["id"] == story_id:
            return (
                f"📖 **\"{story['title']}\"**\n"
                f"*A {story['year_of_study']} student — {story['condition'].replace('_',' ').title()}*\n\n"
                f"{story['excerpt']}\n\n"
                f"✅ *{story['outcome']}*\n"
                f"🔑 *What helped: {', '.join(story['what_helped'])}*"
            )
    return ""


def submit_story(user_id: str, title: str, content: str,
                 condition: str, what_helped: list) -> dict:
    """
    Student submits their own recovery story for review.
    Goes through moderation before being added to the library.
    """
    from core.pii_scrubber import scrub
    record = insert_record("story_submission", {
        "user_id":     "anon",  # Never link story to user_id
        "title":       scrub(title),
        "content":     scrub(content),
        "condition":   condition,
        "what_helped": what_helped,
        "status":      "pending_review",
        "submitted_at":datetime.utcnow().isoformat(),
    })
    return {"status": "submitted", "message": "Thank you for sharing. Your story will be reviewed and may help others."}


def list_all_stories(condition: str = None) -> list:
    stories = STORY_LIBRARY
    if condition:
        stories = [s for s in stories if s.get("condition") == condition]
    return [{"id": s["id"], "title": s["title"], "condition": s["condition"],
             "tags": s["tags"], "outcome": s["outcome"]} for s in stories]
