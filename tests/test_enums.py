from __future__ import annotations

import pytest

from src.gatekeeper.utils.enums import Confidence, Severity


@pytest.mark.parametrize("higher,lower", [
    (Severity.CRITICAL, Severity.HIGH),
    (Severity.HIGH, Severity.MEDIUM),
    (Severity.MEDIUM, Severity.LOW),
    (Severity.LOW, Severity.INFO),
])
def test_severity_ordering(higher, lower):
    assert higher > lower
    assert higher >= lower
    assert lower < higher
    assert lower <= higher
    assert higher >= higher
    assert lower <= lower


@pytest.mark.parametrize("higher,lower", [
    (Confidence.HIGH, Confidence.MEDIUM),
    (Confidence.MEDIUM, Confidence.LOW),
])
def test_confidence_ordering(higher, lower):
    assert higher > lower
    assert higher >= lower
    assert lower < higher
    assert lower <= higher
    assert higher >= higher
    assert lower <= lower
