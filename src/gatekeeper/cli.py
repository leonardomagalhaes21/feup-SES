import sys
from pathlib import Path

import click

from src.gatekeeper.config import load_config
from src.gatekeeper.policy.engine import PolicyEngine
from src.gatekeeper.reporter.terminal import TerminalReporter
from src.gatekeeper.scanner import run_all_scanners
from src.gatekeeper.utils.enums import Decision
from src.gatekeeper.utils.types import PolicyResults


@click.group()
@click.version_option(package_name="security-gatekeeper")
def main():
    """Security Gatekeeper -- Catch vulnerabilities before they reach your pipeline."""


@main.command()
@click.option(
    "--target",
    required=True,
    type=click.Path(exists=True, file_okay=True, dir_okay=True, resolve_path=True),
    help="Path to the project or file to scan.",
)
@click.option(
    "--config",
    "config_path",
    default=None,
    type=click.Path(exists=True, resolve_path=True),
    help="Path to a custom gatekeeper.yaml configuration file.",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["terminal", "json"], case_sensitive=False),
    default="terminal",
    help="Output format for scan results.",
)
def scan(target: str, config_path: str | None, output_format: str):
    """Run security scanners against the target and apply policy rules."""
    config = load_config(config_path)
    target_path = Path(target)

    click.echo(f"Scanning target: {target_path}\n")

    findings = run_all_scanners(target_path, config)

    if not findings:
        click.echo("No findings detected. You're good to go!")
        sys.exit(0)

    engine = PolicyEngine.from_config(config)
    evaluated: PolicyResults = engine.evaluate_all(findings)

    if output_format == "terminal":
        reporter = TerminalReporter(root_path=target_path)
        reporter.report(evaluated)

    has_blocks = any(decision == Decision.BLOCK for _, decision in evaluated)
    sys.exit(1 if has_blocks else 0)


