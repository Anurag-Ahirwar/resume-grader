import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixtures.extracted_samples import (
    complete_extracted, empty_extracted, multi_page_extracted,
    narrow_margins_extracted, wide_margins_extracted, unbalanced_margins_extracted,
    inconsistent_fonts_extracted,
)

from parser_engine.scoring.scorers import formatting


def test_complete_resume_scores_high():
    data = complete_extracted()
    result = formatting.score(data["raw_text"], data)
    assert result.raw_score >= 80
    assert result.bucket_id == "formatting"
    assert result.weight == 0.20


def test_empty_resume_scores_low_with_findings():
    data = empty_extracted()
    result = formatting.score(data["raw_text"], data)
    assert result.raw_score <= 40
    assert any(f.type == "negative" for f in result.findings)


def test_multi_page_resume_loses_page_points():
    complete = formatting.score(complete_extracted()["raw_text"], complete_extracted())
    multi = formatting.score(multi_page_extracted()["raw_text"], multi_page_extracted())
    assert multi.raw_score < complete.raw_score
    assert any(f.criterion == "page_count" for f in multi.findings)


def test_narrow_margins_flagged():
    data = narrow_margins_extracted()
    result = formatting.score(data["raw_text"], data)
    margin_findings = [f for f in result.findings if f.criterion == "margins"]
    assert margin_findings
    assert any("Narrow" in f.message for f in margin_findings)


def test_wide_margins_flagged():
    data = wide_margins_extracted()
    result = formatting.score(data["raw_text"], data)
    margin_findings = [f for f in result.findings if f.criterion == "margins"]
    assert any("Excessive" in f.message for f in margin_findings)


def test_unbalanced_margins_flagged():
    data = unbalanced_margins_extracted()
    result = formatting.score(data["raw_text"], data)
    margin_findings = [f for f in result.findings if f.criterion == "margins"]
    assert any("Unbalanced" in f.message for f in margin_findings)


def test_inconsistent_fonts_flagged():
    data = inconsistent_fonts_extracted()
    result = formatting.score(data["raw_text"], data)
    font_findings = [f for f in result.findings if f.criterion == "font_consistency"]
    assert font_findings


def test_severity_assigned_to_negative_findings():
    data = empty_extracted()
    result = formatting.score(data["raw_text"], data)
    negatives = [f for f in result.findings if f.type == "negative"]
    assert negatives
    assert all(f.severity is not None for f in negatives)
