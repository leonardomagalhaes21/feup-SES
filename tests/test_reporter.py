from __future__ import annotations

from rich.console import Console

from src.gatekeeper.reporter.terminal import TerminalReporter
from src.gatekeeper.utils.enums import Decision, Severity


def test_terminal_reporter_summary_and_location(tmp_path, finding_factory):
    root = tmp_path
    absolute_file = root / "app.py"

    reporter = TerminalReporter(root_path=root)
    reporter.console = Console(record=True, width=120)

    blocked = finding_factory(severity=Severity.HIGH, file=str(absolute_file), line=7)
    warned = finding_factory(severity=Severity.MEDIUM, file=str(absolute_file), line=11)
    allowed = finding_factory(severity=Severity.LOW, file=str(absolute_file), line=13)

    evaluated = [
        (blocked, Decision.BLOCK),
        (warned, Decision.WARN),
        (allowed, Decision.ALLOW),
    ]

    reporter.report(evaluated)

    output = reporter.console.export_text()

    assert "Result: BLOCKED" in output
    assert "Blocked: 1" in output
    assert reporter._format_location(blocked).endswith("app.py:7")
