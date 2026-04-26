from __future__ import annotations

from pathlib import Path
from typing import Any

from src.gatekeeper.scanner.base import BaseScanner
from src.gatekeeper.scanner.finding import Finding
from src.gatekeeper.utils.enums import Category, Confidence, Severity


class BanditScanner(BaseScanner):
    """Runs Bandit (Python-specific SAST) and normalises output."""

    def __init__(self, config: dict[str, Any]):
        cfg = config.get("bandit", {})
        self._min_confidence: str = cfg.get("confidence", Confidence.MEDIUM)

    def name(self) -> str:
        return "bandit"

    def scan(self, target: Path) -> list[Finding]:
        ignored_paths = self._get_ignored_paths(target)
        bandit_ignored = []
        for p in ignored_paths:
            bandit_ignored.extend([p, f"{p}/*", f"*/{p}/*"])
        ignored = ",".join(bandit_ignored)

        cmd = [
            "bandit", "-r", str(target),
            "-f", "json",
            "-x", ignored,
            "--confidence-level", self._min_confidence.lower(),
            "--quiet",
        ]

        raw = self._run_command(cmd)
        return self._normalise(raw)

    def _normalise(self, raw: dict) -> list[Finding]:
        findings = []
        for issue in raw.get("results", []):
            cwe = issue.get("issue_cwe", {})
            cwe_str = f"CWE-{cwe['id']}" if isinstance(cwe, dict) and cwe.get("id") else None
            raw_severity = issue.get("issue_severity", Severity.MEDIUM).upper()
            raw_confidence = issue.get("issue_confidence", Confidence.MEDIUM).upper()

            findings.append(Finding(
                id=issue.get("test_id", "unknown"),
                scanner="bandit",
                severity=Severity(raw_severity) if raw_severity in Severity else Severity.MEDIUM,
                cwe=cwe_str,
                confidence=Confidence(raw_confidence) if raw_confidence in Confidence else Confidence.MEDIUM,
                category=Category.SAST,
                title=issue.get("issue_text", "")[:120],
                description=issue.get("issue_text", ""),
                file=issue.get("filename"),
                line=issue.get("line_number"),
                rule_id=issue.get("test_id", ""),
                extra={
                    "test_name": issue.get("test_name"),
                    "line_range": issue.get("line_range"),
                    "code": issue.get("code"),
                },
            ))
        return findings
