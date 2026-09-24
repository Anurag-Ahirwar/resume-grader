import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixtures.extracted_samples import complete_extracted, missing_projects_and_experience_extracted

from parser_engine.scoring.scorers import experience


def test_complete_experience_scores_high():
    result = experience.score(complete_extracted())
    # NOTE: preserved V1 regex quirk: r"\b\d+[%]\b" never matches "30%\n" because \b
    # requires a word/non-word transition immediately after "%", and "%" followed by
    # whitespace/newline is non-word -> non-word (no transition). So the measurable-outcome
    # bonus doesn't apply here even though "30%" is present; only the section (+50) and
    # year (+20) bonuses land, for 70.
    assert result.raw_score == 70


def test_no_experience_scores_low():
    result = experience.score(missing_projects_and_experience_extracted())
    assert result.raw_score < 70
    assert any(f.criterion == "experience_section" for f in result.findings)
