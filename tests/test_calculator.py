import pytest

from parser_engine.scoring.calculator import calculate_overall_score
from parser_engine.scoring.contract import BucketScore
from parser_engine.scoring.config import SCORING_VERSION


def _bucket(bucket_id, raw_score, weight):
    return BucketScore(bucket_id=bucket_id, name=bucket_id, raw_score=raw_score, weight=weight)


def test_all_perfect_buckets_score_100_regardless_of_weight_total():
    # This is the core V2 fix: weights summing to 0.85 must no longer cap the max score.
    buckets = [
        _bucket("formatting", 100, 0.20),
        _bucket("contact", 100, 0.10),
        _bucket("education", 100, 0.10),
        _bucket("technical_skills", 100, 0.15),
        _bucket("soft_skills", 100, 0.05),
        _bucket("projects", 100, 0.15),
        _bucket("experience", 100, 0.10),
    ]
    result = calculate_overall_score(buckets)
    assert result.overall_score == 100.0
    assert result.weight_total == pytest.approx(0.85)
    assert result.scoring_version == SCORING_VERSION


def test_all_zero_buckets_score_0():
    buckets = [_bucket("formatting", 0, 0.20), _bucket("contact", 0, 0.10)]
    result = calculate_overall_score(buckets)
    assert result.overall_score == 0.0


def test_normalization_matches_v1_divided_by_085():
    # A resume that scored 69 under the old (buggy) unnormalized V1 formula should score
    # 69/0.85 ~= 81.2 under V2, since raw bucket scores and weight ratios are unchanged.
    buckets = [
        _bucket("formatting", 95, 0.20),
        _bucket("contact", 100, 0.10),
        _bucket("education", 100, 0.10),
        _bucket("technical_skills", 60, 0.15),
        _bucket("soft_skills", 60, 0.05),
        _bucket("projects", 75, 0.15),
        _bucket("experience", 70, 0.10),
    ]
    v1_style_overall = sum(b.raw_score * b.weight for b in buckets)  # what V1 computed (no division)
    result = calculate_overall_score(buckets)
    assert result.overall_score == pytest.approx(v1_style_overall / 0.85, abs=0.1)


def test_deterministic_same_input_same_output():
    buckets = [_bucket("formatting", 82, 0.20), _bucket("contact", 61, 0.10)]
    r1 = calculate_overall_score(buckets)
    r2 = calculate_overall_score(buckets)
    assert r1.overall_score == r2.overall_score
    assert r1.weight_total == r2.weight_total


def test_overall_score_clamped_to_0_100():
    buckets = [_bucket("formatting", 100, 1.0)]
    result = calculate_overall_score(buckets)
    assert 0.0 <= result.overall_score <= 100.0


def test_empty_bucket_list_raises():
    with pytest.raises(ValueError):
        calculate_overall_score([])
