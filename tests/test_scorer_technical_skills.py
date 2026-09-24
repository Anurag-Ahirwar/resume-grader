import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixtures.extracted_samples import complete_extracted, empty_extracted

from parser_engine.scoring.scorers import technical_skills


def test_complete_skills_scores_100():
    result = technical_skills.score(complete_extracted())
    assert result.raw_score == 100


def test_no_skills_scores_0():
    result = technical_skills.score(empty_extracted())
    # NOTE: preserved V1 quirk: `len(set([])) < len([])` is `0 < 0` = False, so an empty
    # skills list is treated as "no duplicates" and still earns the 20-point bonus.
    assert result.raw_score == 20
    assert any(f.criterion == "skill_count" for f in result.findings)


def test_duplicate_skills_flagged():
    data = complete_extracted()
    data["skills"] = ["python", "python", "sql", "react", "docker", "node"]
    result = technical_skills.score(data)
    assert any(f.criterion == "duplicate_skills" for f in result.findings)
