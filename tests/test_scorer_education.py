import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fixtures.extracted_samples import complete_extracted, missing_education_extracted

from parser_engine.scoring.scorers import education


def test_complete_education_scores_100():
    result = education.score(complete_extracted())
    assert result.raw_score == 100


def test_missing_education_scores_low():
    result = education.score(missing_education_extracted())
    # NOTE: "github.com" contains the substring "b.com" (one of the degree keywords), a
    # preserved V1 regex false-positive (see V2 execution plan design notes on preserving
    # existing rule logic as-is) -- it silently satisfies the degree-keyword checks even
    # though there's no real degree text, so no findings fire here, just a lower score
    # from the missing "education section" 40 points.
    assert result.raw_score == 60
