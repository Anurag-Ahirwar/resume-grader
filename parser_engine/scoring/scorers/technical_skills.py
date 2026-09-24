"""Technical Skills bucket scorer. Rules unchanged from V1 scoring_engine.py."""
from typing import List

from ..contract import BucketScore, Finding
from ..config import BUCKET_NAMES, BUCKET_WEIGHTS

BUCKET_ID = "technical_skills"
_TOP_LANGS = ["python", "java", "javascript", "c++", "sql", "react", "node"]


def score(extracted: dict) -> BucketScore:
    skills = extracted.get("skills", [])
    total = 0
    findings: List[Finding] = []

    if len(skills) >= 5:
        total += 40
    elif len(skills) > 0:
        total += 20
    else:
        findings.append(_neg("skill_count", "Missing technical skills",
                             "Add relevant technical skills (Python, SQL, etc.).", impact=40))

    if any(sl.lower() in _TOP_LANGS for sl in skills):
        total += 40

    if len(set(skills)) < len(skills):
        findings.append(_neg("duplicate_skills", "Duplicate skills detected",
                             "Avoid repeating skills.", impact=20))
    else:
        total += 20

    raw_score = max(0.0, min(100.0, float(total)))
    return BucketScore(
        bucket_id=BUCKET_ID, name=BUCKET_NAMES[BUCKET_ID], raw_score=raw_score,
        weight=BUCKET_WEIGHTS[BUCKET_ID], findings=findings,
    )


def _neg(criterion, message, feedback, impact=None) -> Finding:
    return Finding(
        criterion=criterion, type="negative", category=BUCKET_NAMES[BUCKET_ID],
        message=message, feedback=feedback, section="skills", impact=impact,
    )
