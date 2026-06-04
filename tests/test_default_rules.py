from __future__ import annotations

from src.gatekeeper.policy.default_rules import (
    rule_critical_severity,
    rule_high_confidence_medium_plus,
    rule_high_dangerous_patterns,
    rule_high_injection,
    rule_low_allow,
    rule_medium_warn,
)
from src.gatekeeper.utils.enums import Confidence, Decision, Severity


def test_default_rules_block_on_critical(finding_factory):
    finding = finding_factory(severity=Severity.CRITICAL)

    assert rule_critical_severity(finding) == Decision.BLOCK


def test_default_rules_block_on_high_injection(finding_factory):
    finding = finding_factory(severity=Severity.HIGH, cwe="CWE-79")

    assert rule_high_injection(finding) == Decision.BLOCK


def test_default_rules_block_on_high_dangerous_patterns(finding_factory):
    finding = finding_factory(severity=Severity.HIGH, cwe="CWE-502")

    assert rule_high_dangerous_patterns(finding) == Decision.BLOCK


def test_default_rules_block_on_high_confidence(finding_factory):
    finding = finding_factory(severity=Severity.MEDIUM, confidence=Confidence.HIGH)

    assert rule_high_confidence_medium_plus(finding) == Decision.BLOCK


def test_default_rules_warn_and_allow(finding_factory):
    medium = finding_factory(severity=Severity.MEDIUM)
    low = finding_factory(severity=Severity.LOW)

    assert rule_medium_warn(medium) == Decision.WARN
    assert rule_low_allow(low) == Decision.ALLOW


def test_rule_critical_severity_returns_none_for_non_critical(finding_factory):
    finding = finding_factory(severity=Severity.HIGH)

    assert rule_critical_severity(finding) is None


def test_rule_high_injection_returns_none_when_cwe_does_not_match(finding_factory):
    finding = finding_factory(severity=Severity.HIGH, cwe="CWE-200")

    assert rule_high_injection(finding) is None


def test_rule_high_injection_returns_none_when_severity_is_not_high(finding_factory):
    finding = finding_factory(severity=Severity.MEDIUM, cwe="CWE-89")

    assert rule_high_injection(finding) is None


def test_rule_high_dangerous_patterns_returns_none_when_cwe_does_not_match(finding_factory):
    finding = finding_factory(severity=Severity.HIGH, cwe="CWE-89")

    assert rule_high_dangerous_patterns(finding) is None


def test_rule_high_confidence_medium_plus_returns_none_for_low_confidence(finding_factory):
    finding = finding_factory(severity=Severity.HIGH, confidence=Confidence.LOW)

    assert rule_high_confidence_medium_plus(finding) is None


def test_rule_medium_warn_returns_none_for_non_medium(finding_factory):
    finding = finding_factory(severity=Severity.LOW)

    assert rule_medium_warn(finding) is None


def test_rule_low_allow_returns_none_for_non_low(finding_factory):
    finding = finding_factory(severity=Severity.HIGH)

    assert rule_low_allow(finding) is None
