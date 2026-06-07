import subprocess
import pytest
from pathlib import Path

@pytest.fixture
def e2e_target(tmp_path):
    # Create an ALLOWED file (Low severity, High confidence)
    allowed_file = tmp_path / "allowed.py"
    allowed_file.write_text("assert True\n")
    
    # Create a WARNING file (Medium severity, Medium confidence)
    warning_file = tmp_path / "warning.py"
    warning_file.write_text("with open('/tmp/test.txt', 'w') as f:\n    f.write('hello')\n")
    
    # Create a BLOCKED file (High severity, High confidence)
    blocked_file = tmp_path / "blocked.py"
    blocked_file.write_text("import os\nos.system('ls ' + 'foo')\n")
    
    return tmp_path, allowed_file, warning_file, blocked_file


def test_e2e_allowed_only(e2e_target):
    tmp_path, allowed_file, _, _ = e2e_target
    # Run gatekeeper specifically on the allowed file
    result = subprocess.run(["uv", "run", "gatekeeper", "scan", "--target", str(allowed_file)], capture_output=True, text=True)
    
    assert result.returncode == 0
    assert "Result: PASSED" in result.stdout
    assert "Allowed: 1" in result.stdout
    assert "Blocked: 0" in result.stdout


def test_e2e_warning_only(e2e_target):
    tmp_path, _, warning_file, _ = e2e_target
    result = subprocess.run(["uv", "run", "gatekeeper", "scan", "--target", str(warning_file)], capture_output=True, text=True)
    
    # Warnings do not block the commit, so returncode is still 0
    assert result.returncode == 0
    assert "Result: PASSED" in result.stdout
    assert "Warnings: 1" in result.stdout
    assert "Blocked: 0" in result.stdout


def test_e2e_blocked_only(e2e_target):
    tmp_path, _, _, blocked_file = e2e_target
    result = subprocess.run(["uv", "run", "gatekeeper", "scan", "--target", str(blocked_file)], capture_output=True, text=True)
    
    # Blocked issues MUST return a non-zero exit code to block the git commit
    assert result.returncode == 1
    assert "Result: BLOCKED" in result.stdout
    assert "Blocked: 1" in result.stdout


def test_e2e_all_combined(e2e_target):
    tmp_path, _, _, _ = e2e_target
    # Run on the whole directory
    result = subprocess.run(["uv", "run", "gatekeeper", "scan", "--target", str(tmp_path)], capture_output=True, text=True)
    
    # Should block because there is at least 1 blocked file
    assert result.returncode == 1
    assert "Result: BLOCKED" in result.stdout
    assert "Blocked: 1" in result.stdout
    assert "Warnings: 1" in result.stdout
    assert "Allowed: 1" in result.stdout
