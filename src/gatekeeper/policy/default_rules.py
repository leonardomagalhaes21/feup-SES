from __future__ import annotations

from src.gatekeeper.scanner.finding import Finding
from src.gatekeeper.utils.enums import Confidence, Decision, Severity

INJECTION_CWES = {"CWE-78", "CWE-89", "CWE-94", "CWE-79"}
DANGEROUS_CWES = {"CWE-502", "CWE-798"}


def rule_critical_severity(finding: Finding) -> Decision | None:
    if finding.severity == Severity.CRITICAL:
        return Decision.BLOCK
    return None


def rule_high_injection(finding: Finding) -> Decision | None:
    if finding.severity == Severity.HIGH and finding.cwe in INJECTION_CWES:
        return Decision.BLOCK
    return None


def rule_high_dangerous_patterns(finding: Finding) -> Decision | None:
    if finding.severity == Severity.HIGH and finding.cwe in DANGEROUS_CWES:
        return Decision.BLOCK
    return None


def rule_high_confidence_medium_plus(finding: Finding) -> Decision | None:
    if finding.confidence == Confidence.HIGH and finding.severity in (Severity.HIGH, Severity.MEDIUM, Severity.CRITICAL):
        return Decision.BLOCK
    return None


def rule_medium_warn(finding: Finding) -> Decision | None:
    if finding.severity == Severity.MEDIUM:
        return Decision.WARN
    return None


def rule_low_allow(finding: Finding) -> Decision | None:
    if finding.severity in (Severity.LOW, Severity.INFO):
        return Decision.ALLOW
    return None


DEFAULT_RULES = [
    rule_critical_severity,
    rule_high_injection,
    rule_high_dangerous_patterns,
    rule_high_confidence_medium_plus,
    rule_medium_warn,
    rule_low_allow,
]
