import pytest

from parser_engine.scoring.config import (
    BUCKET_WEIGHTS,
    InvalidScoringConfig,
    validate_weights,
    weight_total,
)


def test_default_config_is_valid():
    validate_weights(BUCKET_WEIGHTS)  # should not raise


def test_default_config_weight_total_is_085():
    # Documented product weights (20+10+10+15+5+15+10) sum to 0.85, not 1.0 -- this is exactly
    # why the calculator normalizes by weight_total instead of assuming it's always 1.0.
    assert weight_total(BUCKET_WEIGHTS) == pytest.approx(0.85)


def test_empty_config_rejected():
    with pytest.raises(InvalidScoringConfig):
        validate_weights({})


def test_negative_weight_rejected():
    with pytest.raises(InvalidScoringConfig):
        validate_weights({"formatting": 0.2, "contact": -0.1})


def test_zero_total_weight_rejected():
    with pytest.raises(InvalidScoringConfig):
        validate_weights({"formatting": 0.0, "contact": 0.0})


def test_missing_bucket_id_rejected():
    with pytest.raises(InvalidScoringConfig):
        validate_weights({"": 0.5, "contact": 0.5})


def test_valid_custom_config_summing_to_one():
    validate_weights({"formatting": 0.5, "contact": 0.5})  # should not raise
