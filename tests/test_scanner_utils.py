from __future__ import annotations

from src.gatekeeper.scanner import normalize_findings
from src.gatekeeper.utils.enums import Confidence, Severity


def test_normalize_findings_deduplicates_and_sorts(finding_factory):
    high = finding_factory(severity=Severity.HIGH, confidence=Confidence.HIGH, file="app.py", line=5)
    low = finding_factory(severity=Severity.LOW, confidence=Confidence.LOW, file="app.py", line=5)
    unlocated = finding_factory(severity=Severity.MEDIUM, file=None, line=None)

    findings = normalize_findings([low, high, unlocated])

    assert len(findings) == 2
    assert findings[0].severity == Severity.HIGH
    assert findings[1].file is None
