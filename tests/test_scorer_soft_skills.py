import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixtures.extracted_samples import complete_extracted, empty_extracted

from parser_engine.scoring.scorers import soft_skills


def test_complete_resume_has_soft_skill_evidence():
    result = soft_skills.score(complete_extracted()["raw_text"])
    assert result.raw_score > 0
    assert result.findings == []


def test_no_soft_skills_scores_0():
    result = soft_skills.score(empty_extracted()["raw_text"])
    assert result.raw_score == 0
    assert any(f.criterion == "soft_skill_keywords" for f in result.findings)
