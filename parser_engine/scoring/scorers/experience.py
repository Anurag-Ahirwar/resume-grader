"""Work Experience bucket scorer. Rules unchanged from V1 scoring_engine.py."""
import re
from typing import List

from ..contract import BucketScore, Finding
from ..config import BUCKET_NAMES, BUCKET_WEIGHTS

BUCKET_ID = "experience"


def score(extracted: dict) -> BucketScore:
    exp_blocks = extracted.get("experience_blocks", [])
    raw = extracted.get("raw_text", "")
    raw_lower = raw.lower()
    total = 0
    findings: List[Finding] = []

    has_exp_section = len(exp_blocks) > 0
    has_exp_in_text = bool(re.search(r"\b(experience|work experience|employment|internship|intern)\b", raw_lower))
    has_job_keywords = bool(re.search(r"\b(worked|developed|managed|led|coordinated|assisted|supported)\b", raw_lower))

    if has_exp_section or (has_exp_in_text and has_job_keywords):
        total += 50
    else:
        findings.append(_neg("experience_section", "No work experience section found",
                             "Add internships or experience entries with responsibilities.", impact=50))

    if re.search(r"\b\d+[%]\b", raw):
        total += 30

    if re.search(r"\b(20\d{2}|19\d{2})\b", raw):
        total += 20

    raw_score = max(0.0, min(100.0, float(total)))
    return BucketScore(
        bucket_id=BUCKET_ID, name=BUCKET_NAMES[BUCKET_ID], raw_score=raw_score,
        weight=BUCKET_WEIGHTS[BUCKET_ID], findings=findings,
    )


def _neg(criterion, message, feedback, impact=None) -> Finding:
    return Finding(
        criterion=criterion, type="negative", category=BUCKET_NAMES[BUCKET_ID],
        message=message, feedback=feedback, section="experience", impact=impact,
    )
