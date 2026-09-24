"""Scoring configuration: bucket weights and validation.

Weights are intentionally NOT required to sum to 100/1.0. The current product weights sum to
0.85 (20+10+10+15+5+15+10), which previously silently capped every resume's overall score at 85/100
(see backend/app/main.py history / V2 execution plan audit). V2 always normalizes by the weight
total in `calculator.calculate_overall_score`, so the *relative* importance of each bucket is
preserved exactly as-is while the overall score correctly reaches 100 for a perfect resume.
"""
from typing import Dict

SCORING_VERSION = "2.0"

# Same 7 buckets and relative weights as the original product spec (README "Comprehensive Scoring System").
BUCKET_WEIGHTS: Dict[str, float] = {
    "formatting": 0.20,
    "contact": 0.10,
    "education": 0.10,
    "technical_skills": 0.15,
    "soft_skills": 0.05,
    "projects": 0.15,
    "experience": 0.10,
}

BUCKET_NAMES: Dict[str, str] = {
    "formatting": "Formatting & Styling",
    "contact": "Contact Information",
    "education": "Education",
    "technical_skills": "Technical Skills",
    "soft_skills": "Soft Skills",
    "projects": "Projects",
    "experience": "Work Experience",
}


class InvalidScoringConfig(ValueError):
    pass


def validate_weights(weights: Dict[str, float]) -> None:
    """Fail loudly on a malformed config. Does not require the total to equal 1.0 — see module docstring."""
    if not weights:
        raise InvalidScoringConfig("Scoring configuration must define at least one bucket.")

    seen = set()
    for bucket_id, weight in weights.items():
        if not bucket_id or not isinstance(bucket_id, str):
            raise InvalidScoringConfig(f"Invalid bucket id: {bucket_id!r}")
        if bucket_id in seen:
            raise InvalidScoringConfig(f"Duplicate bucket id in scoring configuration: {bucket_id!r}")
        seen.add(bucket_id)
        if weight is None or weight < 0:
            raise InvalidScoringConfig(
                f"Invalid weight for bucket {bucket_id!r}: {weight!r}. Weights must be >= 0."
            )

    if weight_total(weights) == 0:
        raise InvalidScoringConfig("Total scoring weight is 0 — at least one bucket must have a positive weight.")


def weight_total(weights: Dict[str, float]) -> float:
    return sum(weights.values())


# Validate the shipped default configuration at import time — fail fast on startup, not mid-request.
validate_weights(BUCKET_WEIGHTS)
