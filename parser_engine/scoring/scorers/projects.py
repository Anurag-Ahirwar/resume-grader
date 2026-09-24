"""Projects bucket scorer. Rules unchanged from V1 scoring_engine.py."""
import re
from typing import List

from ..contract import BucketScore, Finding
from ..config import BUCKET_NAMES, BUCKET_WEIGHTS

BUCKET_ID = "projects"
_PROJECT_KEYWORDS = ["github", "built", "developed", "dashboard", "application", "system", "model"]
_ACTION_VERBS = ["developed", "built", "designed", "implemented", "created", "built a", "developed a"]


def score(extracted: dict) -> BucketScore:
    projects = extracted.get("projects", [])
    raw = extracted.get("raw_text", "")
    raw_lower = raw.lower()
    total = 0
    findings: List[Finding] = []

    has_projects_section = len(projects) > 0
    has_projects_in_text = bool(re.search(r"\b(project|projects)\b", raw_lower))
    has_project_keywords = any(kw in raw_lower for kw in _PROJECT_KEYWORDS)

    if has_projects_section:
        if len(projects) >= 2:
            total += 50
        elif len(projects) == 1:
            total += 25
    elif has_projects_in_text and has_project_keywords:
        total += 30
    else:
        findings.append(_neg("project_count", "No projects found",
                             "Add at least 1-2 technical projects with clear description.", impact=50))

    if any(v in raw_lower for v in _ACTION_VERBS):
        total += 30
    else:
        if has_projects_section or has_projects_in_text:
            total += 15
        else:
            findings.append(_neg("action_verbs", "Missing action verbs",
                                 "Use strong action verbs in project descriptions.", impact=30))

    if len(str(raw)) > 200:
        total += 20

    raw_score = max(0.0, min(100.0, float(total)))
    return BucketScore(
        bucket_id=BUCKET_ID, name=BUCKET_NAMES[BUCKET_ID], raw_score=raw_score,
        weight=BUCKET_WEIGHTS[BUCKET_ID], findings=findings,
    )


def _neg(criterion, message, feedback, impact=None) -> Finding:
    return Finding(
        criterion=criterion, type="negative", category=BUCKET_NAMES[BUCKET_ID],
        message=message, feedback=feedback, section="projects", impact=impact,
    )
