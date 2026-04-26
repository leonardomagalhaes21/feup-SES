from __future__ import annotations

from dataclasses import dataclass, field

from src.gatekeeper.utils.enums import Category, Confidence, Severity


@dataclass
class Finding:
    """A single security finding in the unified schema."""

    id: str
    scanner: str
    severity: Severity
    cwe: str | None = None
    confidence: Confidence = Confidence.MEDIUM
    category: Category = Category.SAST

    title: str = ""
    description: str = ""

    file: str | None = None
    line: int | None = None

    rule_id: str = ""
    extra: dict = field(default_factory=dict)
