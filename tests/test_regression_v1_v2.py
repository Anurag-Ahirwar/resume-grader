"""Regression comparison: V1 (pre-normalization) vs V2 (normalized) scoring engine,
per the V2 execution plan's Phase 20. The old parser_engine/scoring_engine.py module was
deleted once its logic moved into parser_engine/scoring/scorers/*, so V1 is loaded here
straight from git history (it's still committed) rather than duplicated as dead code.

Every overall-score delta between V1 and V2 must be explained by the known 0.85 -> 1.0
normalization fix (see parser_engine/scoring/config.py docstring) -- not some other
unexplained drift in the refactor.
"""
import subprocess
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixtures.extracted_samples import ALL_FIXTURES

from parser_engine.scoring import score_resume

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_v1_scoring_engine():
    # The file is gone from HEAD once its logic has moved into parser_engine/scoring/. `git log`
    # still lists the deleting commit itself as having "touched" the path, so walk commits
    # (newest first) and use the first one whose tree still actually contains the file.
    commits = subprocess.run(
        ["git", "log", "--all", "--format=%H", "--", "parser_engine/scoring_engine.py"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.split()

    for commit in commits:
        result = subprocess.run(
            ["git", "show", f"{commit}:parser_engine/scoring_engine.py"],
            cwd=REPO_ROOT, capture_output=True, text=True,
        )
        if result.returncode == 0:
            module = types.ModuleType("_v1_scoring_engine_baseline")
            exec(compile(result.stdout, f"scoring_engine.py (V1, from {commit[:8]})", "exec"), module.__dict__)
            return module

    pytest.skip("parser_engine/scoring_engine.py (V1 baseline) not found anywhere in git history")


V1_WEIGHTS = [
    ("Formatting & Styling", "score_formatting_and_styling", 0.20, True),
    ("Contact Information", "score_contact_info", 0.10, False),
    ("Education", "score_education", 0.10, False),
    ("Technical Skills", "score_technical_skills", 0.15, False),
    ("Soft Skills", "score_soft_skills", 0.05, "raw_text_only"),
    ("Projects", "score_projects", 0.15, False),
    ("Work Experience", "score_work_experience", 0.10, False),
]


def _v1_overall(v1, extracted):
    raw_text = extracted["raw_text"]
    total = 0.0
    for _, fn_name, weight, mode in V1_WEIGHTS:
        fn = getattr(v1, fn_name)
        if mode is True:
            score_val, _ = fn(raw_text, extracted)
        elif mode == "raw_text_only":
            score_val, _ = fn(raw_text)
        else:
            score_val, _ = fn(extracted)
        total += score_val * weight
    return int(total)  # V1 truncated to int, never divided by weight total (the bug)


@pytest.fixture(scope="module")
def v1():
    return _load_v1_scoring_engine()


@pytest.mark.parametrize("fixture_name", list(ALL_FIXTURES.keys()))
def test_v2_overall_equals_v1_divided_by_weight_total(v1, fixture_name):
    extracted = ALL_FIXTURES[fixture_name]()
    if not extracted["raw_text"].strip():
        pytest.skip("empty-resume fixture: V1's int() truncation vs V2's rounding diverge trivially at 0")

    v1_overall = _v1_overall(v1, extracted)
    v2_result = score_resume(extracted["raw_text"], extracted)

    expected_v2 = v1_overall / 0.85
    # Generous tolerance: V1 truncates to int per-bucket-sum, V2 rounds the final result to 1dp.
    assert v2_result.overall_score == pytest.approx(expected_v2, abs=1.5), (
        f"[{fixture_name}] V1={v1_overall} (/0.85={expected_v2:.1f}) vs V2={v2_result.overall_score} "
        "-- unexplained by the normalization fix alone"
    )
    assert v2_result.overall_score >= v1_overall  # normalization should never make scores worse
