"""
services/ngo_manager.py — NGO & Low-Cost Psychologist Management System.

Three responsibilities:
  1. FINANCIAL FILTER: Match students to NGOs/therapists they can afford
  2. EXPANDED DATABASE: Structured database ready to grow as you onboard more partners
  3. EMAIL OUTREACH: Auto-draft partnership emails to send to prospective NGOs/therapists

Why this exists:
  Your plan: "collect more data from local mental health institutions,
  shortlist based on financial criteria, reach out personally through email."
  This module IS that system — automated where possible, human-curated where it must be.
"""

from datetime import datetime
from data.db import insert_record, query_records


# ─────────────────────────────────────────────────────────────────────────────
# EXPANDED NGO + THERAPIST DATABASE
# Structure supports: cost tiers, languages, specialties, online/offline,
# verification status, and outreach history.
# ─────────────────────────────────────────────────────────────────────────────

FULL_NGO_DATABASE = [

    # ── Verified Partners, with full contact and eligibility fields ─
    {
        "id": "sangath",
        "name": "Sangath",
        "type": "ngo",
        "verified": True,
        "specialty": ["depression", "anxiety", "ptsd", "general"],
        "city": "Pan-India",
        "state": "Pan-India",
        "online": True,
        "offline": False,
        "languages": ["English", "Hindi", "Konkani"],
        "contact_email": "contactus@sangath.in",
        "contact_phone": "011-41708155",
        "website": "https://sangath.in",
        "cost_per_session_inr": 0,
        "cost_tier": "free",          # free | subsidised | low_cost | standard
        "cost_notes": "Fully free for students",
        "max_wait_days": 7,
        "partnership_status": "active",   # prospect | contacted | negotiating | active | declined
        "outreach_sent": True,
        "rating": 4.5,
        "student_reviews": 23,
    },
    {
        "id": "afa",
        "name": "Action for Autism (AFA) India",
        "type": "ngo",
        "verified": True,
        "specialty": ["autism", "adhd", "sensory", "developmental"],
        "city": "Delhi",
        "state": "Delhi",
        "online": False,
        "offline": True,
        "languages": ["English", "Hindi"],
        "contact_email": "actionforautism@gmail.com",
        "contact_phone": "011-40504437",
        "website": "https://autism-india.org",
        "cost_per_session_inr": 0,
        "cost_tier": "free",
        "cost_notes": "Free consultations for diagnosis referral",
        "max_wait_days": 14,
        "partnership_status": "active",
        "outreach_sent": True,
        "rating": 4.7,
        "student_reviews": 11,
    },
    {
        "id": "vandrevala",
        "name": "Vandrevala Foundation",
        "type": "ngo",
        "verified": True,
        "specialty": ["crisis", "depression", "anxiety", "general"],
        "city": "Pan-India",
        "state": "Pan-India",
        "online": True,
        "offline": False,
        "languages": ["English", "Hindi", "Marathi", "Kannada", "Tamil", "Telugu"],
        "contact_email": "info@vandrevalafoundation.com",
        "contact_phone": "1860-2662-345",
        "website": "https://www.vandrevalafoundation.com",
        "cost_per_session_inr": 0,
        "cost_tier": "free",
        "cost_notes": "24/7 free helpline",
        "max_wait_days": 0,
        "partnership_status": "active",
        "outreach_sent": True,
        "rating": 4.3,
        "student_reviews": 47,
    },
    {
        "id": "icall",
        "name": "iCall (TISS Mumbai)",
        "type": "ngo",
        "verified": True,
        "specialty": ["depression", "anxiety", "stress", "relationships", "academic"],
        "city": "Mumbai",
        "state": "Maharashtra",
        "online": True,
        "offline": True,
        "languages": ["English", "Hindi"],
        "contact_email": "icall@tiss.edu",
        "contact_phone": "9152987821",
        "website": "https://icallhelpline.org",
        "cost_per_session_inr": 0,
        "cost_tier": "free",
        "cost_notes": "Free for students",
        "max_wait_days": 3,
        "partnership_status": "active",
        "outreach_sent": True,
        "rating": 4.6,
        "student_reviews": 38,
    },
    {
        "id": "nimhans_tele",
        "name": "NIMHANS Tele-manas (Kiran Helpline)",
        "type": "government",
        "verified": True,
        "specialty": ["general", "crisis", "all"],
        "city": "Pan-India",
        "state": "Pan-India",
        "online": True,
        "offline": False,
        "languages": ["Hindi", "Tamil", "Telugu", "Kannada", "Malayalam", "Bengali",
                      "Odia", "Assamese", "Gujarati", "Marathi", "Punjabi", "Urdu", "English"],
        "contact_email": "nimhans@nic.in",
        "contact_phone": "1800-599-0019",
        "website": "https://nimhans.ac.in",
        "cost_per_session_inr": 0,
        "cost_tier": "free",
        "cost_notes": "Free, 24/7, government-funded",
        "max_wait_days": 0,
        "partnership_status": "active",
        "outreach_sent": True,
        "rating": 4.2,
        "student_reviews": 91,
    },

    # ── Prospects (to be contacted) ────────────────────────────────────────────
    {
        "id": "lissun",
        "name": "Lissun",
        "type": "platform",
        "verified": False,
        "specialty": ["depression", "anxiety", "relationships", "grief"],
        "city": "Pan-India",
        "state": "Pan-India",
        "online": True,
        "offline": False,
        "languages": ["English", "Hindi"],
        "contact_email": "hello@lissun.app",
        "contact_phone": "",
        "website": "https://lissun.app",
        "cost_per_session_inr": 500,
        "cost_tier": "low_cost",
        "cost_notes": "Sessions from ₹500, student discount available",
        "max_wait_days": 2,
        "partnership_status": "prospect",
        "outreach_sent": False,
        "rating": None,
        "student_reviews": 0,
    },
    {
        "id": "yuvamanas",
        "name": "Yuva Manas",
        "type": "ngo",
        "verified": False,
        "specialty": ["youth", "depression", "anxiety", "academic", "bullying"],
        "city": "Bengaluru",
        "state": "Karnataka",
        "online": True,
        "offline": True,
        "languages": ["English", "Hindi", "Kannada"],
        "contact_email": "support@yuvamanas.org",
        "contact_phone": "",
        "website": "https://yuvamanas.org",
        "cost_per_session_inr": 0,
        "cost_tier": "free",
        "cost_notes": "Free for college students",
        "max_wait_days": 5,
        "partnership_status": "prospect",
        "outreach_sent": False,
        "rating": None,
        "student_reviews": 0,
    },
    {
        "id": "mpowerminds",
        "name": "MPower Minds",
        "type": "platform",
        "verified": False,
        "specialty": ["depression", "anxiety", "adhd", "ocd", "bipolar"],
        "city": "Mumbai",
        "state": "Maharashtra",
        "online": True,
        "offline": True,
        "languages": ["English", "Hindi", "Marathi"],
        "contact_email": "connect@mpowerminds.com",
        "contact_phone": "1800-120-820050",
        "website": "https://mpowerminds.com",
        "cost_per_session_inr": 800,
        "cost_tier": "low_cost",
        "cost_notes": "₹800–1500/session, subsidised slots available",
        "max_wait_days": 3,
        "partnership_status": "prospect",
        "outreach_sent": False,
        "rating": None,
        "student_reviews": 0,
    },
    {
        "id": "ngo_anti_bullying",
        "name": "Cyberbullying Research & Support India (iAmHuman)",
        "type": "ngo",
        "verified": False,
        "specialty": ["bullying", "cyberbullying", "harassment", "ragging"],
        "city": "Pan-India",
        "state": "Pan-India",
        "online": True,
        "offline": False,
        "languages": ["English", "Hindi"],
        "contact_email": "support@iamhuman.in",
        "contact_phone": "",
        "website": "https://iamhuman.in",
        "cost_per_session_inr": 0,
        "cost_tier": "free",
        "cost_notes": "Free online counseling for bullying victims",
        "max_wait_days": 3,
        "partnership_status": "prospect",
        "outreach_sent": False,
        "rating": None,
        "student_reviews": 0,
    },
]

COST_TIER_ORDER = ["free", "subsidised", "low_cost", "standard"]


# ─────────────────────────────────────────────────────────────────────────────
# FINANCIAL FILTER
# ─────────────────────────────────────────────────────────────────────────────


def _build_contact(ngo: dict) -> str:
    """Build a unified contact string from contact_phone and contact_email."""
    parts = []
    if ngo.get("contact_phone"):
        parts.append(ngo["contact_phone"])
    if ngo.get("contact_email"):
        parts.append(ngo["contact_email"])
    return " | ".join(parts) if parts else "See website"


def _enrich(ngo: dict) -> dict:
    """Add computed 'contact' field so callers can use ngo['contact'] safely."""
    if "contact" not in ngo:
        ngo = dict(ngo)
        ngo["contact"] = _build_contact(ngo)
    return ngo


def find_affordable_support(
    condition: str = "",
    max_cost_inr: int = 0,
    prefer_online: bool = True,
    language: str = "",
    city: str = "",
    limit: int = 3,
) -> list[dict]:
    """
    Find NGOs/therapists matching a student's financial constraint and needs.

    Args:
        condition:    Specialty keyword (e.g. 'adhd', 'bullying', 'depression')
        max_cost_inr: Maximum budget per session in INR (0 = free only)
        prefer_online: Prefer online-capable providers
        language:     Preferred language
        city:         Student's city (for offline matches)
        limit:        Max results to return

    Returns:
        Sorted list of matching providers (best match first).
    """
    results = []

    for ngo in FULL_NGO_DATABASE:
        # Financial filter (hard cutoff)
        cost = ngo.get("cost_per_session_inr", 0)
        if max_cost_inr == 0 and cost > 0:
            continue
        if max_cost_inr > 0 and cost > max_cost_inr:
            continue

        # Online preference
        if prefer_online and not ngo.get("online"):
            continue

        # Score: specialty match, language match, city match, verified
        score = 0
        cond_lower = condition.lower()
        specialty_str = " ".join(ngo.get("specialty", []))
        if cond_lower and cond_lower in specialty_str:
            score += 3
        if language and language.lower() in [l.lower() for l in ngo.get("languages", [])]:
            score += 2
        if city and city.lower() in ngo.get("city", "").lower():
            score += 2
        if ngo.get("verified"):
            score += 1
        if ngo.get("partnership_status") == "active":
            score += 2
        # Prefer providers with lower wait times
        wait = ngo.get("max_wait_days", 99)
        if wait == 0:
            score += 2
        elif wait <= 3:
            score += 1

        results.append({**ngo, "_match_score": score})

    results.sort(key=lambda x: (-x["_match_score"],
                                COST_TIER_ORDER.index(x.get("cost_tier", "standard"))))
    return [_enrich(r) for r in results[:limit]]


def get_prospects_for_outreach() -> list[dict]:
    """Return all NGOs marked as 'prospect' that haven't been contacted yet."""
    return [n for n in FULL_NGO_DATABASE
            if n.get("partnership_status") == "prospect"
            and not n.get("outreach_sent")]


def mark_outreach_sent(ngo_id: str, method: str = "email") -> bool:
    """Record that outreach was sent to an NGO."""
    insert_record("ngo_outreach", {
        "ngo_id": ngo_id,
        "method": method,
        "ts": datetime.utcnow().isoformat(),
        "status": "sent",
    })
    # Update in-memory record
    for ngo in FULL_NGO_DATABASE:
        if ngo["id"] == ngo_id:
            ngo["outreach_sent"] = True
            ngo["partnership_status"] = "contacted"
            return True
    return False


def get_ngo_by_id(ngo_id: str) -> dict | None:
    for ngo in FULL_NGO_DATABASE:
        if ngo["id"] == ngo_id:
            return _enrich(ngo)
    return None


# ─────────────────────────────────────────────────────────────────────────────
# EMAIL OUTREACH DRAFT GENERATOR
# ─────────────────────────────────────────────────────────────────────────────

def draft_outreach_email(ngo_id: str, sender_name: str = "SentinelMind Team",
                         sender_college: str = "Our College") -> dict:
    """
    Generate a professional partnership outreach email draft for an NGO/therapist.
    Returns subject + body as strings ready to copy/send.

    Why AI-generated: Every NGO gets a personalised email mentioning their
    specialty — generic bulk emails have very low response rates.
    """
    ngo = get_ngo_by_id(ngo_id)
    if not ngo:
        return {"error": f"NGO '{ngo_id}' not found"}

    specialties = ", ".join(ngo.get("specialty", ["mental health"])[:3])
    cost_note = (
        "free or subsidised" if ngo["cost_tier"] in ("free", "subsidised")
        else f"low-cost (₹{ngo['cost_per_session_inr']} per session)"
    )
    languages = ", ".join(ngo.get("languages", ["English"])[:4])

    subject = (
        f"Partnership Proposal: SentinelMind × {ngo['name']} — "
        f"Digital Mental Health for College Students"
    )

    body = f"""Dear {ngo['name']} Team,

I hope this message finds you well.

My name is {sender_name}, and I am writing on behalf of SentinelMind — a privacy-first, 
AI-powered mental health support platform designed specifically for Indian college students.

We are currently a student innovation project from {sender_college}, addressing the critical 
gap in campus mental health support. Our platform provides:

  • 24/7 confidential AI first-aid with clinical screening tools (PHQ-9, GAD-7, GHQ-12, AQ-10, ASRS)
  • Automatic escalation to human counselors for high-risk students
  • Peer support network and IoT-based distress monitoring
  • Coverage for broader needs including autism, ADHD, and Down syndrome support
  • WhatsApp-based access for low-bandwidth environments

We specifically reached out to {ngo['name']} because of your focus on {specialties} and 
your {cost_note} model — which aligns perfectly with our mission to make mental health 
support accessible to every student, regardless of their financial situation.

We would love to explore a formal referral partnership where:

  1. SentinelMind identifies and triages students who need professional support
  2. Students are connected to your services through our confidential booking system
  3. You receive anonymised, structured intake data (with student consent) to make 
     your first session more effective

This partnership costs you nothing — we bring you pre-screened, consenting students, 
and you provide the professional support that complements our AI-first-aid model.

We serve students across {languages} and are committed to cultural sensitivity in 
our support model.

Would you be open to a 20-minute introductory call to explore this further? 
I would be happy to give you a live demonstration of the platform.

Thank you sincerely for the important work you do.

Warm regards,

{sender_name}
SentinelMind — Team Crusade Codex
Email: sentinelmind@project.edu
Platform: [Your ngrok/hosted URL]

---
This email was drafted using SentinelMind's partnership outreach system.
Reply directly to this email to get in touch with our team.
"""

    # Log that we drafted (not sent yet)
    insert_record("ngo_outreach", {
        "ngo_id": ngo_id,
        "ngo_name": ngo["name"],
        "method": "email_draft",
        "ts": datetime.utcnow().isoformat(),
        "status": "drafted",
    })

    return {
        "ngo_id": ngo_id,
        "ngo_name": ngo["name"],
        "to_email": ngo.get("contact_email", ""),
        "subject": subject,
        "body": body,
        "status": "draft",
        "note": "Review and personalise before sending. Mark as sent after dispatch.",
    }


def draft_all_prospect_emails(sender_name: str = "SentinelMind Team",
                               sender_college: str = "Our College") -> list[dict]:
    """Draft emails for ALL prospects not yet contacted."""
    prospects = get_prospects_for_outreach()
    return [draft_outreach_email(p["id"], sender_name, sender_college) for p in prospects]


def add_new_ngo(ngo_data: dict) -> dict:
    """Add a newly discovered NGO/therapist to the database for review."""
    required = ["name", "contact_email", "specialty"]
    for field in required:
        if not ngo_data.get(field):
            return {"error": f"Missing required field: {field}"}

    ngo_data.setdefault("id", ngo_data["name"].lower().replace(" ", "_")[:20])
    ngo_data.setdefault("verified", False)
    ngo_data.setdefault("partnership_status", "prospect")
    ngo_data.setdefault("outreach_sent", False)
    ngo_data.setdefault("cost_tier", "unknown")

    FULL_NGO_DATABASE.append(ngo_data)
    insert_record("ngo_submission", {"submitted": ngo_data, "ts": datetime.utcnow().isoformat()})
    return {"status": "added", "ngo_id": ngo_data["id"]}
