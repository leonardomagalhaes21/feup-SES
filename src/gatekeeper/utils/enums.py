from __future__ import annotations

from enum import StrEnum

_SEVERITY_RANK: dict[str, int] = {
    "CRITICAL": 5,
    "HIGH": 4,
    "MEDIUM": 3,
    "LOW": 2,
    "INFO": 1,
}

class Severity(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

    def __lt__(self, other: Severity) -> bool:
        return _SEVERITY_RANK[self] < _SEVERITY_RANK[other]

    def __le__(self, other: Severity) -> bool:
        return _SEVERITY_RANK[self] <= _SEVERITY_RANK[other]

    def __gt__(self, other: Severity) -> bool:
        return _SEVERITY_RANK[self] > _SEVERITY_RANK[other]

    def __ge__(self, other: Severity) -> bool:
        return _SEVERITY_RANK[self] >= _SEVERITY_RANK[other]


_CONFIDENCE_RANK: dict[str, int] = {
    "HIGH": 3,
    "MEDIUM": 2,
    "LOW": 1,
}

class Confidence(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

    def __lt__(self, other: Confidence) -> bool:
        return _CONFIDENCE_RANK[self] < _CONFIDENCE_RANK[other]

    def __le__(self, other: Confidence) -> bool:
        return _CONFIDENCE_RANK[self] <= _CONFIDENCE_RANK[other]

    def __gt__(self, other: Confidence) -> bool:
        return _CONFIDENCE_RANK[self] > _CONFIDENCE_RANK[other]

    def __ge__(self, other: Confidence) -> bool:
        return _CONFIDENCE_RANK[self] >= _CONFIDENCE_RANK[other]


class Category(StrEnum):
    SAST = "sast"
    DEPENDENCY = "dependency"
    SECRET = "secret"


class Decision(StrEnum):
    BLOCK = "BLOCK"
    WARN = "WARN"
    ALLOW = "ALLOW"
