"""Soft Skills bucket scorer. Rules unchanged from V1 scoring_engine.py.

Conservative by design (per V2 execution plan Phase 10): scores presence of documented
evidence of soft-skill keywords, not an inferred judgment of the candidate's actual abilities.
"""
from typing import List

from ..contract import BucketScore, Finding
from ..config import BUCKET_NAMES, BUCKET_WEIGHTS

BUCKET_ID = "soft_skills"
_SOFT_KEYWORDS = ["communication", "leadership", "teamwork", "collaboration", "problem solving", "critical thinking"]


def score(raw_text: str) -> BucketScore:
    lower = raw_text.lower()
    present = [s for s in _SOFT_KEYWORDS if s in lower]
    raw_score = float(min(100, len(present) * 20))
    findings: List[Finding] = []

    if raw_score == 0:
        findings.append(Finding(
            criterion="soft_skill_keywords", type="negative", category=BUCKET_NAMES[BUCKET_ID],
            message="Soft skills missing",
            feedback="Add soft skills such as teamwork, leadership, or communication.",
            section="soft_skills", impact=20,
        ))

    return BucketScore(
        bucket_id=BUCKET_ID, name=BUCKET_NAMES[BUCKET_ID], raw_score=raw_score,
        weight=BUCKET_WEIGHTS[BUCKET_ID], findings=findings,
    )
