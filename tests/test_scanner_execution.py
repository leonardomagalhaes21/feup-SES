from __future__ import annotations

import subprocess
from pathlib import Path
import pytest

from src.gatekeeper.scanner import _run_single_scanner, run_all_scanners
from src.gatekeeper.scanner.base import BaseScanner
from src.gatekeeper.scanner.scanners.bandit import BanditScanner
from src.gatekeeper.scanner.scanners.semgrep import SemgrepScanner
from src.gatekeeper.scanner.scanners.trivy import TrivyScanner

P = lambda out, code=0: type("P", (), {"stdout": out, "returncode": code, "stderr": "err"})


class DummyScanner(BaseScanner):
    name = lambda s: "dummy"
    scan = lambda s, t: []


def test_base_scanner_methods(tmp_path, monkeypatch):
    scanner = DummyScanner()

    monkeypatch.setattr("shutil.which", lambda n: "/bin/dummy")
    assert scanner.is_available() is True
    monkeypatch.setattr("shutil.which", lambda n: None)
    assert scanner.is_available() is False

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: P("ignored_dir/\nanother_ignored/"))
    ignored = scanner._get_ignored_paths(tmp_path)
    assert "ignored_dir" in ignored and ".git" in ignored

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: exec("raise FileNotFoundError()"))
    assert scanner._get_ignored_paths(tmp_path) == [".git", "__pycache__", ".tox", ".eggs", ".venv"]

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: P('{"res": 1}', 0))
    assert scanner._run_command(["cmd"]) == {"res": 1}

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: P('{"res": 2}', 1))
    assert scanner._run_command(["cmd"]) == {"res": 2}

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: P("", 2))
    with pytest.raises(RuntimeError):
        scanner._run_command(["cmd"])


def test_run_single_scanner(finding_factory):
    s = DummyScanner()
    s.scan = lambda t: [finding_factory(id="F-SUCCESS")]
    name, findings, elapsed, error = _run_single_scanner(s, Path("."))
    assert name == "dummy" and len(findings) == 1 and findings[0].id == "F-SUCCESS" and error is None

    f = DummyScanner()
    def raise_err(target): raise ValueError("failed")
    f.scan = raise_err
    name, findings, elapsed, error = _run_single_scanner(f, Path("."))
    assert len(findings) == 0 and "failed" in error


def test_run_all_scanners_scenarios(monkeypatch, finding_factory):
    config_disabled = {"scanners": {"semgrep": {"enabled": False}, "bandit": {"enabled": False}, "trivy": {"enabled": False}}}
    assert run_all_scanners(Path("."), config_disabled) == []

    config_enabled = {"scanners": {"semgrep": {"enabled": True}, "bandit": {"enabled": True}, "trivy": {"enabled": True}}}
    monkeypatch.setattr(SemgrepScanner, "is_available", lambda s: False)
    monkeypatch.setattr(BanditScanner, "is_available", lambda s: False)
    monkeypatch.setattr(TrivyScanner, "is_available", lambda s: False)
    assert run_all_scanners(Path("."), config_enabled) == []

    monkeypatch.setattr(SemgrepScanner, "is_available", lambda s: True)
    monkeypatch.setattr(BanditScanner, "is_available", lambda s: True)
    monkeypatch.setattr(TrivyScanner, "is_available", lambda s: True)
    monkeypatch.setattr(SemgrepScanner, "scan", lambda s, t: [finding_factory(id="semgrep-1")])
    monkeypatch.setattr(BanditScanner, "scan", lambda s, t: [finding_factory(id="bandit-1")])
    monkeypatch.setattr(TrivyScanner, "scan", lambda s, t: [finding_factory(id="trivy-1")])

    findings = run_all_scanners(Path("."), config_enabled)
    assert {f.id for f in findings} == {"semgrep-1", "bandit-1", "trivy-1"}

    config_single = {"scanners": {"semgrep": {"enabled": True}, "bandit": {"enabled": False}, "trivy": {"enabled": False}}}
    monkeypatch.setattr(SemgrepScanner, "scan", lambda s, t: exec("raise Exception('failed')"))
    assert run_all_scanners(Path("."), config_single) == []


def test_concrete_scanners_config_and_commands():
    bandit = BanditScanner({"bandit": {"confidence": "HIGH"}})
    assert bandit._min_confidence == "HIGH"
    bandit._get_ignored_paths = lambda t: ["venv"]
    bandit._run_command = lambda cmd, t=120: setattr(bandit, "last_cmd", cmd) or {"results": []}
    bandit.scan(Path("target"))
    assert "-x" in bandit.last_cmd and "venv/*" in bandit.last_cmd[bandit.last_cmd.index("-x") + 1]

    semgrep = SemgrepScanner({"semgrep": {"rulesets": ["p/ci", "p/default"]}})
    assert semgrep._rulesets == ["p/ci", "p/default"]
    semgrep._get_ignored_paths = lambda t: ["venv"]
    semgrep._run_command = lambda cmd, t=120: setattr(semgrep, "last_cmd", cmd) or {"results": []}
    semgrep.scan(Path("target"))
    assert "--config" in semgrep.last_cmd and "p/ci" in semgrep.last_cmd and "--exclude" in semgrep.last_cmd

    trivy = TrivyScanner({"trivy": {"scan_type": "image"}})
    assert trivy._scan_type == "image"
    trivy._get_ignored_paths = lambda t: ["venv"]
    trivy._run_command = lambda cmd, t=120: setattr(trivy, "last_cmd", cmd) or {"Results": []}
    trivy.scan(Path("target"))
    assert "image" in trivy.last_cmd and "--skip-dirs" in trivy.last_cmd
