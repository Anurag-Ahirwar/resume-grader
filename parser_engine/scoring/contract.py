"""Data contracts for the V2 scoring engine: Finding, BucketScore, OverallResult."""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


def severity_for_impact(impact: Optional[int]) -> Severity:
    """Map a point deduction to a severity tier. impact is expected as a positive magnitude."""
    if impact is None:
        return Severity.LOW
    magnitude = abs(impact)
    if magnitude >= 20:
        return Severity.CRITICAL
    if magnitude >= 15:
        return Severity.HIGH
    if magnitude >= 8:
        return Severity.MEDIUM
    return Severity.LOW


@dataclass
class Finding:
    """A single scored observation: either a deduction (negative) or a satisfied criterion (positive)."""
    criterion: str
    type: str  # "positive" | "negative"
    category: str  # bucket display name, kept for backward-compat with the old `mistakes` API field
    message: str
    feedback: str
    section: Optional[str] = None
    severity: Optional[Severity] = None
    value: Optional[str] = None
    expected: Optional[str] = None
    impact: Optional[int] = None

    def __post_init__(self):
        if self.type == "negative" and self.severity is None:
            self.severity = severity_for_impact(self.impact)


@dataclass
class BucketScore:
    bucket_id: str
    name: str
    raw_score: float  # 0-100
    weight: float  # 0-1, e.g. 0.20
    max_score: float = 100.0
    findings: List[Finding] = field(default_factory=list)

    @property
    def weighted_score(self) -> float:
        return self.raw_score * self.weight


@dataclass
class OverallResult:
    overall_score: float  # 0-100
    scoring_version: str
    weight_total: float
    buckets: List[BucketScore]
