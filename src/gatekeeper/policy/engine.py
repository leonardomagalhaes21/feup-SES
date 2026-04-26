from __future__ import annotations

from typing import Any

from src.gatekeeper.policy.default_rules import DEFAULT_RULES
from src.gatekeeper.scanner.finding import Finding
from src.gatekeeper.utils.enums import Decision
from src.gatekeeper.utils.types import PolicyResults, PolicyRule


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
        """Build a PolicyEngine using the default rules and config."""
        policy_cfg = config.get("policy", {})
        raw_default = policy_cfg.get("default_action", Decision.WARN).upper()
        default_action = Decision(raw_default) if raw_default in Decision else Decision.WARN
        return cls(rules=DEFAULT_RULES, default_action=default_action)
