from __future__ import annotations

from src.gatekeeper.policy.engine import PolicyEngine
from src.gatekeeper.utils.enums import Category, Confidence, Decision, Severity


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


def test_policy_engine_uses_default_rules_when_no_rules_in_config(finding_factory):
    engine = PolicyEngine.from_config({})
    finding = finding_factory(severity=Severity.CRITICAL)

    assert engine.evaluate(finding) == Decision.BLOCK


def test_rule_from_dict_matches_on_confidence(finding_factory):
    config = {
        "policy": {
            "rules": [{"decision": "BLOCK", "confidence": "HIGH"}],
        }
    }

    engine = PolicyEngine.from_config(config)
    assert engine.evaluate(finding_factory(confidence=Confidence.HIGH)) == Decision.BLOCK
    assert engine.evaluate(finding_factory(confidence=Confidence.LOW)) == Decision.WARN


def test_rule_from_dict_matches_on_category(finding_factory):
    config = {
        "policy": {
            "rules": [{"decision": "BLOCK", "category": "dependency"}],
        }
    }

    engine = PolicyEngine.from_config(config)
    assert engine.evaluate(finding_factory(category=Category.DEPENDENCY)) == Decision.BLOCK
    assert engine.evaluate(finding_factory(category=Category.SAST)) == Decision.WARN


def test_rule_from_dict_no_match_when_cwe_absent(finding_factory):
    config = {
        "policy": {
            "rules": [{"decision": "BLOCK", "cwe": ["CWE-89"]}],
        }
    }

    engine = PolicyEngine.from_config(config)
    finding = finding_factory(cwe=None)

    assert engine.evaluate(finding) == Decision.WARN


def test_rule_from_dict_no_match_when_severity_mismatch(finding_factory):
    config = {
        "policy": {
            "rules": [{"decision": "BLOCK", "severity": "HIGH"}],
        }
    }

    engine = PolicyEngine.from_config(config)
    finding = finding_factory(severity=Severity.LOW)

    assert engine.evaluate(finding) == Decision.WARN

