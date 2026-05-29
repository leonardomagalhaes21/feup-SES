from __future__ import annotations

from click.testing import CliRunner

from src.gatekeeper.cli import main
from src.gatekeeper.policy.engine import PolicyEngine
from src.gatekeeper.scanner.finding import Finding
from src.gatekeeper.utils.enums import Decision, Severity


def test_scan_no_findings_exits_zero(tmp_path, monkeypatch):
    def fake_run_all_scanners(target, config):
        return []

    monkeypatch.setattr("src.gatekeeper.cli.load_config", lambda *_: {})
    monkeypatch.setattr("src.gatekeeper.cli.run_all_scanners", fake_run_all_scanners)

    runner = CliRunner()
    result = runner.invoke(main, ["scan", "--target", str(tmp_path)])

    assert result.exit_code == 0
    assert "No findings detected" in result.output


def test_scan_blocked_exits_one(tmp_path, monkeypatch):
    finding = Finding(
        id="F-1",
        scanner="unit",
        severity=Severity.HIGH,
        cwe="CWE-79",
        file=str(tmp_path / "app.py"),
        line=1,
    )

    def fake_run_all_scanners(target, config):
        return [finding]

    def fake_normalize(findings):
        return findings

    def fake_from_config(cls, config):
        return PolicyEngine(rules=[], default_action=Decision.BLOCK)

    monkeypatch.setattr("src.gatekeeper.cli.load_config", lambda *_: {})
    monkeypatch.setattr("src.gatekeeper.cli.run_all_scanners", fake_run_all_scanners)
    monkeypatch.setattr("src.gatekeeper.cli.normalize_findings", fake_normalize)
    monkeypatch.setattr("src.gatekeeper.cli.PolicyEngine.from_config", classmethod(fake_from_config))

    runner = CliRunner()
    result = runner.invoke(main, ["scan", "--target", str(tmp_path)])

    assert result.exit_code == 1
