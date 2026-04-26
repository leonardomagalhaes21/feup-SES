from __future__ import annotations

from pathlib import Path
from typing import Any

from src.gatekeeper.scanner.base import BaseScanner
from src.gatekeeper.scanner.finding import Finding
from src.gatekeeper.utils.enums import Category, Confidence, Severity

SEVERITY_MAP = {
    "ERROR": Severity.HIGH,
    "WARNING": Severity.MEDIUM,
    "INFO": Severity.LOW,
}


class SemgrepScanner(BaseScanner):
    """Runs Semgrep with configurable rulesets and normalises output."""

    def __init__(self, config: dict[str, Any]):
        cfg = config.get("semgrep", {})
        self._rulesets: list[str] = cfg.get("rulesets", ["p/security-audit"])

    def name(self) -> str:
        return "semgrep"

    def scan(self, target: Path) -> list[Finding]:
        cmd = ["semgrep", "--json", "--quiet"]
        for ruleset in self._rulesets:
            cmd.extend(["--config", ruleset])
        cmd.append(str(target))

        raw = self._run_command(cmd)
        return self._normalise(raw)

    def _normalise(self, raw: dict) -> list[Finding]:
        findings = []
        for r in raw.get("results", []):
            extra = r.get("extra", {})
            metadata = extra.get("metadata", {})

            cwe = metadata.get("cwe")
            if isinstance(cwe, list):
                cwe = cwe[0] if cwe else None

            raw_confidence = metadata.get("confidence", Confidence.MEDIUM).upper()

            findings.append(Finding(
                id=r.get("check_id", "unknown"),
                scanner="semgrep",
                severity=SEVERITY_MAP.get(extra.get("severity", "WARNING").upper(), Severity.MEDIUM),
                cwe=cwe,
                confidence=Confidence(raw_confidence) if raw_confidence in Confidence else Confidence.MEDIUM,
                category=Category.SAST,
                title=extra.get("message", "")[:120],
                description=extra.get("message", ""),
                file=r.get("path"),
                line=r.get("start", {}).get("line"),
                rule_id=r.get("check_id", ""),
            ))
        return findings
