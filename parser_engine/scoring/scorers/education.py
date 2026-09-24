"""Education bucket scorer. Rules unchanged from V1 scoring_engine.py."""
import re
from typing import List

from ..contract import BucketScore, Finding
from ..config import BUCKET_NAMES, BUCKET_WEIGHTS

BUCKET_ID = "education"

_DEGREE_KEYWORDS = [
    "btech", "b.tech", "be ", "b.e", "bachelor", "bachelors",
    "mtech", "m.tech", "master", "masters",
    "msc", "m.sc", "bsc", "b.sc",
    "mba", "m.b.a",
    "bba", "b.b.a",
    "bca", "b.c.a",
    "bcom", "b.com",
    "ba ", "b.a ",
    "ma ", "m.a ",
]
_DEGREE_KEYWORDS_EXTENDED = _DEGREE_KEYWORDS + [
    "bachelors of", "bachelor of",
    "master of business administration",
    "master of computer applications",
    "computer science", "artificial intelligence", "data science",
]


def score(extracted: dict) -> BucketScore:
    sections = extracted.get("sections_found", [])
    raw = extracted.get("raw_text", "")
    raw_lower = raw.lower()
    total = 0
    findings: List[Finding] = []

    has_edu_section = any("education" in s.lower() for s in sections)
    has_edu_in_text = bool(re.search(r"\b(education|educational)\b", raw_lower))

    if has_edu_section or has_edu_in_text:
        total += 40
    else:
        has_degree_content = any(k in raw_lower for k in _DEGREE_KEYWORDS)
        if not has_degree_content:
            findings.append(_neg("education_section", "Missing education section",
                                 "Add an education section with degree, institute, and year.", impact=40))

    if any(k in raw_lower for k in _DEGREE_KEYWORDS_EXTENDED):
        total += 40
    else:
        findings.append(_neg(
            "degree_keywords", "Degree keywords not clearly detected",
            "Ensure your degree names are clearly written (e.g. 'B.Tech in CSE', 'MBA in Marketing', 'BCA').",
            impact=40,
        ))

    if re.search(r"\b(20\d{2}|19\d{2})\b", raw):
        total += 20
    else:
        findings.append(_neg("graduation_year", "Missing year details",
                             "Include graduation year (e.g. 2023).", impact=20))

    raw_score = max(0.0, min(100.0, float(total)))
    return BucketScore(
        bucket_id=BUCKET_ID, name=BUCKET_NAMES[BUCKET_ID], raw_score=raw_score,
        weight=BUCKET_WEIGHTS[BUCKET_ID], findings=findings,
    )


def _neg(criterion, message, feedback, impact=None) -> Finding:
    return Finding(
        criterion=criterion, type="negative", category=BUCKET_NAMES[BUCKET_ID],
        message=message, feedback=feedback, section="education", impact=impact,
    )
