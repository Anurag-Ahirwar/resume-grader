from .calculator import calculate_overall_score
from .config import SCORING_VERSION, BUCKET_WEIGHTS, InvalidScoringConfig, validate_weights
from .contract import BucketScore, Finding, OverallResult, Severity
from .scorers import contact, education, experience, formatting, projects, soft_skills, technical_skills


def score_resume(raw_text: str, extracted: dict) -> OverallResult:
    """Run all 7 bucket scorers and compute the overall weighted/normalized result."""
    bucket_scores = [
        formatting.score(raw_text, extracted),
        contact.score(extracted),
        education.score(extracted),
        technical_skills.score(extracted),
        soft_skills.score(raw_text),
        projects.score(extracted),
        experience.score(extracted),
    ]
    return calculate_overall_score(bucket_scores)


__all__ = [
    "calculate_overall_score", "score_resume",
    "SCORING_VERSION", "BUCKET_WEIGHTS", "InvalidScoringConfig", "validate_weights",
    "BucketScore", "Finding", "OverallResult", "Severity",
]
