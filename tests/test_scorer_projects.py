import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixtures.extracted_samples import complete_extracted, missing_projects_and_experience_extracted

from parser_engine.scoring.scorers import projects


def test_complete_projects_scores_high():
    result = projects.score(complete_extracted())
    assert result.raw_score >= 80


def test_no_projects_scores_low():
    result = projects.score(missing_projects_and_experience_extracted())
    assert result.raw_score < 50
    assert any(f.criterion == "project_count" for f in result.findings)
