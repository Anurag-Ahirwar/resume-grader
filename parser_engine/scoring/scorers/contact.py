"""Contact Information bucket scorer. Rules unchanged from V1 scoring_engine.py."""
import re
from typing import List

from ..contract import BucketScore, Finding
from ..config import BUCKET_NAMES, BUCKET_WEIGHTS

BUCKET_ID = "contact"

_PHONE_FALLBACK = re.compile(r"(\+?\d{1,3}[-.\s]?)?(\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}")
_EMAIL_FALLBACK = re.compile(r"[a-zA-Z0-9.\-+_]+@[a-zA-Z0-9.\-+_]+\.[a-zA-Z]+")
_LINKEDIN_FALLBACK = re.compile(r"(linkedin\.com\/in\/[A-Za-z0-9\-\_]+)", re.IGNORECASE)
_GITHUB_FALLBACK = re.compile(r"(github\.com\/[A-Za-z0-9\-\_]+)", re.IGNORECASE)


def score(extracted: dict) -> BucketScore:
    contact = extracted.get("contact", {})
    raw_text = extracted.get("raw_text", "")
    total = 0
    findings: List[Finding] = []

    if contact.get("phones"):
        total += 30
    elif _PHONE_FALLBACK.search(raw_text):
        total += 30
    else:
        findings.append(_neg("phone", "Phone number missing",
                             "Add a reachable phone number so recruiters can easily contact you.", impact=30))

    if contact.get("emails"):
        total += 30
    elif _EMAIL_FALLBACK.search(raw_text):
        total += 30
    else:
        findings.append(_neg("email", "Email missing",
                             "Include a professional email address.", impact=30))

    if contact.get("linkedin"):
        total += 20
    elif _LINKEDIN_FALLBACK.search(raw_text):
        total += 20
    else:
        findings.append(_neg("linkedin", "LinkedIn not found",
                             "Add a LinkedIn profile link to strengthen your professional presence.", impact=20))

    if contact.get("github"):
        total += 20
    elif _GITHUB_FALLBACK.search(raw_text):
        total += 20
    else:
        findings.append(_neg("github", "GitHub not found",
                             "Add a GitHub link to showcase your projects and contributions.", impact=20))

    raw_score = max(0.0, min(100.0, float(total)))
    return BucketScore(
        bucket_id=BUCKET_ID, name=BUCKET_NAMES[BUCKET_ID], raw_score=raw_score,
        weight=BUCKET_WEIGHTS[BUCKET_ID], findings=findings,
    )


def _neg(criterion, message, feedback, impact=None) -> Finding:
    return Finding(
        criterion=criterion, type="negative", category=BUCKET_NAMES[BUCKET_ID],
        message=message, feedback=feedback, section="contact", impact=impact,
    )
