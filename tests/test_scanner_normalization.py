from __future__ import annotations

from src.gatekeeper.scanner.scanners.bandit import BanditScanner
from src.gatekeeper.scanner.scanners.semgrep import SemgrepScanner
from src.gatekeeper.scanner.scanners.trivy import TrivyScanner
from src.gatekeeper.utils.enums import Category, Confidence, Severity


def test_bandit_normalise_maps_fields():
    scanner = BanditScanner({})

    raw = {
        "results": [
            {
                "test_id": "B101",
                "issue_severity": "HIGH",
                "issue_confidence": "LOW",
                "issue_cwe": {"id": 79},
                "issue_text": "Use of assert",
                "filename": "app.py",
                "line_number": 12,
                "test_name": "assert_used",
                "line_range": [12, 13],
                "code": "assert False",
            }
        ]
    }

    findings = scanner._normalise(raw)

    assert findings[0].severity == Severity.HIGH
    assert findings[0].confidence == Confidence.LOW
    assert findings[0].cwe == "CWE-79"
    assert findings[0].category == Category.SAST


def test_semgrep_normalise_maps_fields():
    scanner = SemgrepScanner({})

    raw = {
        "results": [
            {
                "check_id": "python.lang.security.eval-used",
                "path": "app.py",
                "start": {"line": 42},
                "extra": {
                    "severity": "ERROR",
                    "message": "Avoid eval",
                    "metadata": {"cwe": ["CWE-95"], "confidence": "HIGH"},
                },
            }
        ]
    }

    findings = scanner._normalise(raw)

    assert findings[0].severity == Severity.HIGH
    assert findings[0].confidence == Confidence.HIGH
    assert findings[0].cwe == "CWE-95"
    assert findings[0].category == Category.SAST


def test_trivy_normalise_maps_fields():
    scanner = TrivyScanner({})

    raw = {
        "Results": [
            {
                "Target": "requirements.txt",
                "Vulnerabilities": [
                    {
                        "PkgName": "Django",
                        "InstalledVersion": "4.2",
                        "VulnerabilityID": "CVE-2024-0001",
                        "Severity": "HIGH",
                        "CweIDs": ["CWE-79"],
                        "Description": "XSS issue",
                        "FixedVersion": "4.2.1",
                    },
                    {
                        "PkgName": "Requests",
                        "InstalledVersion": "2.0",
                        "VulnerabilityID": "CVE-2024-0002",
                        "Severity": "UNKNOWN",
                        "CweIDs": [],
                        "Description": "Unknown",
                        "FixedVersion": None,
                    },
                ],
            }
        ]
    }

    findings = scanner._normalise(raw)

    assert findings[0].severity == Severity.HIGH
    assert findings[0].cwe == "CWE-79"
    assert findings[0].category == Category.DEPENDENCY
    assert findings[1].severity == Severity.INFO
    assert findings[1].cwe is None
