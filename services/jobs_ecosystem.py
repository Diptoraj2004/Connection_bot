"""
services/jobs_ecosystem.py — Jobs Created By SentinelMind.

THE PROBLEM: "This creates jobs" is meaningless without specifics.

ACTUAL JOBS THIS SYSTEM CREATES:

1. PEER SUPPORT COORDINATORS (campus staff)
   - Manage volunteer training programs
   - Review volunteer performance and assign cases
   - Bridge between AI triage and human counselors
   - 1 per 500 students = significant campus employment

2. REGIONAL LANGUAGE CONTENT SPECIALISTS
   - Translate and validate clinical guidelines in Hindi/Tamil/Telugu/Bengali
   - Review AI responses in regional languages for cultural accuracy
   - Remote work, part-time — accessible to graduates across India

3. NGO LIAISON OFFICERS
   - Onboard new NGO partners (we pay commission per referral)
   - Verify NGO credentials and maintain quality ratings
   - Field-based role — works across Tier 2/3 cities

4. DATA REVIEWERS (anonymous trend analysis)
   - Review anonymised aggregate trends for institutional reports
   - Flag anomalies in escalation patterns
   - Contract-based, remote-friendly

5. COUNSELOR NETWORK MANAGERS
   - Recruit, train, and supervise the platform's counselor network
   - Handle complaints and quality control
   - Full-time role within SentinelMind's operations team

6. STUDENT VOLUNTEER TRAINERS
   - Train peer support volunteers in crisis recognition
   - Certify volunteers at Level 1/2/3
   - Paid per training cohort — freelance model

7. CAMPUS IMPLEMENTATION PARTNERS
   - Help colleges integrate SentinelMind into their systems
   - Technical setup + staff training
   - Reseller model — partners earn per college onboarded

8. RESEARCH ASSOCIATES
   - Work with academic institutions using anonymised data
   - Publish findings that validate the platform clinically
   - Grant-funded initially, then industry-funded

This module handles: volunteer job listings, application, training certification,
NGO partner onboarding, counselor network management.
"""
from datetime import datetime
from data.db import insert_record, query_records


# ── Job Listings ──────────────────────────────────────────────────────────────

JOB_ROLES = {
    "peer_support_coordinator": {
        "title":        "Peer Support Coordinator",
        "type":         "campus_staff",
        "pay_model":    "salary",
        "pay_range":    "₹15,000–25,000/month",
        "requirements": ["Completed any degree", "Empathy training", "No clinical license needed"],
        "responsibilities": [
            "Manage 10–20 trained peer volunteers",
            "Assign volunteers to student cases",
            "Escalate to counselors when needed",
            "Maintain volunteer wellbeing",
        ],
        "creates_per": "1 per 500 students",
    },
    "language_specialist": {
        "title":        "Regional Language Content Specialist",
        "type":         "remote_contract",
        "pay_model":    "per_piece",
        "pay_range":    "₹500–1,500 per validated guideline translation",
        "requirements": ["Native speaker of target language", "Psychology background preferred"],
        "responsibilities": [
            "Translate clinical guidelines to regional languages",
            "Review AI responses for cultural accuracy",
            "Flag culturally inappropriate suggestions",
        ],
        "creates_per": "1–2 per language supported",
    },
    "ngo_liaison": {
        "title":        "NGO Partnership Liaison",
        "type":         "field_staff",
        "pay_model":    "salary_plus_commission",
        "pay_range":    "₹18,000–30,000/month + ₹2,000 per NGO onboarded",
        "requirements": ["Social work background preferred", "Tier 2/3 city presence"],
        "responsibilities": [
            "Identify and approach local NGOs and therapists",
            "Verify credentials and negotiate partnership terms",
            "Maintain NGO quality ratings",
        ],
        "creates_per": "1 per 5 districts covered",
    },
    "volunteer_trainer": {
        "title":        "Student Peer Volunteer Trainer",
        "type":         "freelance",
        "pay_model":    "per_cohort",
        "pay_range":    "₹3,000–8,000 per training cohort of 10 volunteers",
        "requirements": ["Psychology/social work graduate", "Crisis intervention certification"],
        "responsibilities": [
            "Deliver Level 1/2/3 peer volunteer training",
            "Assess and certify volunteers",
            "Provide ongoing supervision",
        ],
        "creates_per": "1 per college per semester",
    },
    "campus_partner": {
        "title":        "Campus Implementation Partner",
        "type":         "reseller",
        "pay_model":    "commission",
        "pay_range":    "15% of annual license fee per college onboarded",
        "requirements": ["EdTech or healthcare background", "Existing college relationships"],
        "responsibilities": [
            "Present SentinelMind to college administrations",
            "Manage technical setup and staff training",
            "Provide first-line support",
        ],
        "creates_per": "Unlimited — entrepreneurial model",
    },
}


def list_job_roles() -> list:
    return [{"role_id": k, **v} for k, v in JOB_ROLES.items()]


def apply_for_role(role_id: str, applicant_name_hash: str,
                   college: str, contact_hash: str,
                   motivation: str = "") -> dict:
    """Submit a job application (all PII hashed before storage)."""
    if role_id not in JOB_ROLES:
        return {"error": f"Unknown role: {role_id}"}
    record = insert_record("job_application", {
        "role_id":            role_id,
        "role_title":         JOB_ROLES[role_id]["title"],
        "applicant_hash":     applicant_name_hash,
        "college":            college,
        "contact_hash":       contact_hash,
        "motivation_preview": motivation[:200],
        "status":             "received",
        "applied_at":         datetime.utcnow().isoformat(),
    })
    return {
        "status":    "application_received",
        "role":      JOB_ROLES[role_id]["title"],
        "reference": record["id"][:8],
        "next":      "Our team will contact you within 5 business days.",
    }


def get_jobs_impact_summary() -> dict:
    """Calculate how many jobs the platform has created."""
    applications = query_records("job_application")
    volunteers   = query_records("volunteer_registration")
    counselors   = query_records("counselor_registration")
    ngos         = query_records("ngo_outreach", {"status": "active"})

    return {
        "job_applications_received": len(applications),
        "active_volunteers":         len(volunteers),
        "registered_counselors":     len(counselors),
        "ngo_partners":              len(ngos),
        "estimated_indirect_jobs":   len(volunteers) + len(counselors) + len(ngos) * 2,
        "roles_available":           len(JOB_ROLES),
        "note": (
            "Every 500 students onboarded creates ~3 jobs: "
            "1 peer coordinator, 1 counselor, 1 NGO liaison."
        ),
    }
