from __future__ import annotations

from typing import Any

from src.gatekeeper.policy.default_rules import DEFAULT_RULES
from src.gatekeeper.scanner.finding import Finding
from src.gatekeeper.utils.enums import Decision
from src.gatekeeper.utils.types import PolicyResults, PolicyRule


def _normalise_list(value: Any) -> list[str] | None:
    """Return a normalised uppercase list, or None if value is absent."""
    if value is None:
        return None
    if isinstance(value, list):
        return [str(v).upper() for v in value]
    return [str(value).upper()]


def _rule_from_dict(rule_dict: dict[str, Any]) -> PolicyRule:
    """Convert a YAML rule dict into a PolicyRule callable.

    Each key (severity, confidence, cwe, category) acts as a match
    condition. A list value means "any of these" (OR). All present
    conditions must match (AND). First matching rule in the chain wins.
    """
    decision = Decision(str(rule_dict["decision"]).upper())
    severities = _normalise_list(rule_dict.get("severity"))
    confidences = _normalise_list(rule_dict.get("confidence"))
    cwes = _normalise_list(rule_dict.get("cwe"))
    categories = _normalise_list(rule_dict.get("category"))

    def rule(finding: Finding) -> Decision | None:
        if severities is not None and finding.severity.upper() not in severities:
            return None
        if confidences is not None and finding.confidence.upper() not in confidences:
            return None
        if cwes is not None and (finding.cwe is None or finding.cwe.upper() not in cwes):
            return None
        if categories is not None and finding.category.upper() not in categories:
            return None
        return decision

    return rule


class PolicyEngine:
    """Evaluates security findings against an ordered rule chain.
    Each rule is a callable that takes a Finding and returns a Decision
    or None (skip to next rule). First match wins.
    """

    def __init__(self, rules: list[PolicyRule], default_action: Decision = Decision.WARN):
        self.rules = rules
        self.default_action = default_action

    def evaluate(self, finding: Finding) -> Decision:
        """Evaluate a single finding."""
        for rule in self.rules:
            decision = rule(finding)
            if decision is not None:
                return decision
        return self.default_action

    def evaluate_all(self, findings: list[Finding]) -> PolicyResults:
        """Evaluate every finding and return (finding, decision) pairs."""
        return [(f, self.evaluate(f)) for f in findings]

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> PolicyEngine:
        """Build a PolicyEngine from config."""
        policy_cfg = config.get("policy", {})
        raw_default = policy_cfg.get("default_action", Decision.WARN).upper()
        default_action = Decision(raw_default) if raw_default in Decision else Decision.WARN

        raw_rules = policy_cfg.get("rules")
        if raw_rules is not None:
            rules: list[PolicyRule] = [_rule_from_dict(r) for r in raw_rules]
        else:
            rules = DEFAULT_RULES

        return cls(rules=rules, default_action=default_action)
