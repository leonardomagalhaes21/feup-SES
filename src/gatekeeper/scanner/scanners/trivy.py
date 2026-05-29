from __future__ import annotations

from pathlib import Path
from typing import Any

from src.gatekeeper.scanner.base import BaseScanner
from src.gatekeeper.scanner.finding import Finding
from src.gatekeeper.utils.enums import Category, Confidence, Severity

SEVERITY_MAP = {"UNKNOWN": Severity.INFO}


class TrivyScanner(BaseScanner):
    """Runs Trivy in filesystem mode to detect vulnerable dependencies."""

    def __init__(self, config: dict[str, Any]):
        cfg = config.get("trivy", {})
        self._scan_type: str = cfg.get("scan_type", "fs")

    def name(self) -> str:
        return "trivy"

    def scan(self, target: Path) -> list[Finding]:
        ignored = ",".join(self._get_ignored_paths(target))
        cmd = ["trivy", self._scan_type, "--skip-dirs", ignored, "--format", "json", "--quiet", str(target)]

        raw = self._run_command(cmd)
        return self._normalise(raw)

    def _normalise(self, raw: dict) -> list[Finding]:
        findings = []
        for target_result in raw.get("Results", []):
            target_name = target_result.get("Target", "unknown")

            for vulnerability in target_result.get("Vulnerabilities", []):
                cwe_ids = vulnerability.get("CweIDs", [])
                pkg = vulnerability.get("PkgName", "?")
                version = vulnerability.get("InstalledVersion", "?")
                vulnerability_id = vulnerability.get("VulnerabilityID", "unknown")
                raw_severity = vulnerability.get("Severity", "UNKNOWN").upper()
                severity = SEVERITY_MAP.get(raw_severity)
                if severity is None:
                    severity = Severity(raw_severity) if raw_severity in Severity else Severity.INFO

                findings.append(Finding(
                    id=vulnerability_id,
                    scanner="trivy",
                    severity=severity,
                    cwe=cwe_ids[0] if cwe_ids else None,
                    confidence=Confidence.HIGH,
                    category=Category.DEPENDENCY,
                    title=f"{pkg}@{version} -> {vulnerability_id}",
                    description=vulnerability.get("Description", ""),
                    file=target_name,
                    line=None,
                    rule_id=vulnerability_id,
                    extra={
                        "pkg_name": pkg,
                        "installed_version": version,
                        "fixed_version": vulnerability.get("FixedVersion"),
                    },
                ))
        return findings
