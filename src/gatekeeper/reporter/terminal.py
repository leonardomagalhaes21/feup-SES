from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.text import Text

from src.gatekeeper.scanner.finding import Finding
from src.gatekeeper.utils.enums import Decision
from src.gatekeeper.utils.types import PolicyResults

DECISION_STYLE = {
    Decision.BLOCK: ("❌", "bold red", "BLOCKED"),
    Decision.WARN:  ("⚠️ ", "bold yellow", "WARNING"),
    Decision.ALLOW: ("ℹ️ ", "dim", "ALLOWED"),
}


class TerminalReporter:
    """Renders evaluated findings as a coloured terminal report."""

    def __init__(self, root_path: Path | None = None):
        self.console = Console()
        self.root_path = root_path

    def report(self, evaluated: PolicyResults):
        self.console.print()
        self.console.rule("[bold cyan]🔍 Security Gatekeeper | Scan Results[/bold cyan]")
        self.console.print()

        self._print_findings(evaluated)
        self._print_summary(evaluated)

    def _print_findings(self, evaluated: PolicyResults):
        blocked, warned, allowed_count = [], [], 0

        for finding, decision in evaluated:
            if decision == Decision.BLOCK:
                blocked.append((finding, decision))
            elif decision == Decision.WARN:
                warned.append((finding, decision))
            elif decision == Decision.ALLOW:
                allowed_count += 1

        if blocked or warned:
            table = Table(show_header=True, header_style="bold", expand=True)
            table.add_column("", width=3)
            table.add_column("Decision", width=10)
            table.add_column("Scanner", width=12)
            table.add_column("CWE", width=10)
            table.add_column("Location", min_width=20, max_width=60, overflow="ellipsis")
            table.add_column("Description")

            for finding, decision in blocked + warned:
                emoji, colour, label = DECISION_STYLE[decision]
                table.add_row(
                    emoji,
                    Text(label, style=colour),
                    finding.scanner,
                    finding.cwe or "—",
                    self._format_location(finding),
                    finding.title,
                )
            self.console.print(table)

        if allowed_count:
            self.console.print(
                f"\nℹ️  [dim]ALLOWED        {allowed_count} finding(s): severity LOW/INFO, policy set to allow[/dim]"
            )

    def _print_summary(self, evaluated: PolicyResults):
        counts = {d: 0 for d in Decision}
        for _, decision in evaluated:
            counts[decision] += 1

        blocked = counts[Decision.BLOCK]
        warned = counts[Decision.WARN]
        allowed = counts[Decision.ALLOW]

        self.console.print()

        if blocked:
            self.console.print(
                f"[bold red]Result: BLOCKED — fix {blocked} critical issue(s) before committing.[/bold red]"
            )
        elif warned:
            self.console.print(
                f"[bold yellow]Result: PASSED with {warned} warning(s). Review recommended.[/bold yellow]"
            )
        else:
            self.console.print("[bold green]Result: PASSED — no issues found.[/bold green]")

        self.console.print(f"  Blocked: {blocked}  |  Warnings: {warned}  |  Allowed: {allowed}")
        self.console.print()

    def _format_location(self, finding: Finding) -> str:
        loc = finding.file or "—"
        if loc != "—" and self.root_path:
            try:
                p = Path(loc)
                if p.is_absolute():
                    loc = str(p.relative_to(self.root_path))
                elif self.root_path.name in p.parts:
                    pass
            except ValueError:
                pass

        if finding.line:
            return f"{loc}:{finding.line}"
        return loc
