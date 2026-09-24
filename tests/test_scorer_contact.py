import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixtures.extracted_samples import complete_extracted, missing_contact_extracted

from parser_engine.scoring.scorers import contact


def test_complete_contact_scores_100():
    result = contact.score(complete_extracted())
    assert result.raw_score == 100
    assert result.findings == []


def test_missing_contact_scores_0_with_four_findings():
    result = contact.score(missing_contact_extracted())
    assert result.raw_score == 0
    criteria = {f.criterion for f in result.findings}
    assert criteria == {"phone", "email", "linkedin", "github"}
    assert all(f.severity is not None for f in result.findings)
