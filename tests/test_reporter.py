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


def test_terminal_reporter_summary_warns_when_no_blocks(tmp_path, finding_factory):
    reporter = TerminalReporter(root_path=tmp_path)
    reporter.console = Console(record=True, width=120)

    finding = finding_factory(severity=Severity.MEDIUM)
    reporter.report([(finding, Decision.WARN)])

    output = reporter.console.export_text()
    assert "PASSED with" in output
    assert "warning" in output


def test_terminal_reporter_summary_passes_when_all_allowed(tmp_path, finding_factory):
    reporter = TerminalReporter(root_path=tmp_path)
    reporter.console = Console(record=True, width=120)

    finding = finding_factory(severity=Severity.LOW)
    reporter.report([(finding, Decision.ALLOW)])

    output = reporter.console.export_text()
    assert "PASSED" in output
    assert "no issues found" in output


def test_format_location_without_line_number(tmp_path, finding_factory):
    reporter = TerminalReporter()

    finding = finding_factory(file="app.py", line=None)

    assert reporter._format_location(finding) == "app.py"
