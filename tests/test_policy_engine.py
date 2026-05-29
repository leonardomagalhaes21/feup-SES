from __future__ import annotations

from src.gatekeeper.policy.engine import PolicyEngine
from src.gatekeeper.utils.enums import Decision, Severity


def test_policy_engine_first_match_wins(finding_factory):
    config = {
        "policy": {
            "default_action": "ALLOW",
            "rules": [
                {"decision": "WARN", "severity": "HIGH"},
                {"decision": "BLOCK", "severity": "HIGH"},
            ],
        }
    }

    engine = PolicyEngine.from_config(config)
    finding = finding_factory(severity=Severity.HIGH)

    assert engine.evaluate(finding) == Decision.WARN


def test_policy_engine_default_action_used(finding_factory):
    config = {"policy": {"default_action": "ALLOW", "rules": []}}

    engine = PolicyEngine.from_config(config)
    finding = finding_factory(severity=Severity.MEDIUM)

    assert engine.evaluate(finding) == Decision.ALLOW


def test_policy_engine_rule_matching(finding_factory):
    config = {
        "policy": {
            "default_action": "WARN",
            "rules": [
                {"decision": "BLOCK", "severity": "HIGH", "cwe": ["CWE-79", "CWE-89"]},
            ],
        }
    }

    engine = PolicyEngine.from_config(config)
    finding = finding_factory(severity=Severity.HIGH, cwe="CWE-79")

    assert engine.evaluate(finding) == Decision.BLOCK
