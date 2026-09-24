"""Central, deterministic overall-score calculation."""
from typing import List

from .config import SCORING_VERSION
from .contract import BucketScore, OverallResult


def calculate_overall_score(bucket_scores: List[BucketScore]) -> OverallResult:
    """overall = Σ(raw_score × weight) / Σ(weight), so a perfect resume always reaches 100
    regardless of whether the configured weights happen to sum to 100.

    Deterministic: identical bucket_scores always produce an identical OverallResult.
    """
    if not bucket_scores:
        raise ValueError("calculate_overall_score requires at least one bucket score.")

    weight_total = sum(b.weight for b in bucket_scores)
    if weight_total <= 0:
        raise ValueError("Total bucket weight must be positive.")

    weighted_sum = sum(b.raw_score * b.weight for b in bucket_scores)
    overall = weighted_sum / weight_total
    overall = max(0.0, min(100.0, overall))

    return OverallResult(
        overall_score=round(overall, 1),
        scoring_version=SCORING_VERSION,
        weight_total=round(weight_total, 4),
        buckets=bucket_scores,
    )
