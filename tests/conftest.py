from __future__ import annotations

import pytest

from src.gatekeeper.scanner.finding import Finding
from src.gatekeeper.utils.enums import Category, Confidence, Severity


@pytest.fixture
def finding_factory():
    def _make(
        *,
        id: str = "F-1",
        scanner: str = "unit",
        severity: Severity = Severity.MEDIUM,
        cwe: str | None = None,
        confidence: Confidence = Confidence.MEDIUM,
        category: Category = Category.SAST,
        file: str | None = "app.py",
        line: int | None = 10,
        title: str = "Issue",
        description: str = "Issue description",
    ) -> Finding:
        return Finding(
            id=id,
            scanner=scanner,
            severity=severity,
            cwe=cwe,
            confidence=confidence,
            category=category,
            title=title,
            description=description,
            file=file,
            line=line,
        )

    return _make
