from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import click

from src.gatekeeper.scanner.base import BaseScanner
from src.gatekeeper.scanner.finding import Finding
from src.gatekeeper.scanner.scanners.bandit import BanditScanner
from src.gatekeeper.scanner.scanners.semgrep import SemgrepScanner
from src.gatekeeper.scanner.scanners.trivy import TrivyScanner


def _run_single_scanner(scanner: BaseScanner, target: Path) -> tuple[str, list[Finding], float, str | None]:
    """Run one scanner and return (name, findings, elapsed, error)."""
    start = time.time()
    try:
        findings = scanner.scan(target)
        return scanner.name(), findings, time.time() - start, None
    except Exception as exc:
        return scanner.name(), [], time.time() - start, str(exc)


def normalize_findings(findings: list[Finding]) -> list[Finding]:
    """Deduplicate findings at the same location, keeping the highest-severity one, then sort by severity."""
    best: dict[tuple, Finding] = {}
    unlocated: list[Finding] = []

    for f in findings:
        if f.file is None or f.line is None:
            unlocated.append(f)
            continue
        key = (f.file, f.line)
        if key not in best or f.severity > best[key].severity:
            best[key] = f

    deduplicated = list(best.values()) + unlocated
    return sorted(deduplicated, key=lambda i: i.severity, reverse=True)


def run_all_scanners(target: Path, config: dict[str, Any]) -> list[Finding]:
    """Instantiate every enabled scanner, run them in parallel, and aggregate findings."""
    scanner_classes: list[type[BaseScanner]] = [
        SemgrepScanner,
        TrivyScanner,
        BanditScanner,
    ]

    scanner_config = config.get("scanners", {})

    scanners_to_run: list[BaseScanner] = []
    for cls in scanner_classes:
        scanner = cls(scanner_config)

        if not scanner_config.get(scanner.name(), {}).get("enabled", True):
            click.echo(f"  [skip] {scanner.name()} -- disabled in config.")
            continue

        if not scanner.is_available():
            click.echo(f"  [skip] {scanner.name()} -- not installed.")
            continue

        scanners_to_run.append(scanner)

    if not scanners_to_run:
        return []

    click.echo(f"  [scan] Running {len(scanners_to_run)} scanner(s) in parallel...")

    all_findings: list[Finding] = []

    with ThreadPoolExecutor(max_workers=len(scanners_to_run)) as pool:
        futures = {
            pool.submit(_run_single_scanner, scanner, target): scanner
            for scanner in scanners_to_run
        }

        for future in as_completed(futures):
            name, findings, elapsed, error = future.result()
            if error:
                click.echo(f"  [fail] {name} failed: {error}")
            else:
                click.echo(f"  [done] {name} -- {len(findings)} finding(s) in {elapsed:.1f}s")
                all_findings.extend(findings)

    return all_findings
