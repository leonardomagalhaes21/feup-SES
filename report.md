# Security Gatekeeper: A Unified, Policy-Driven Security Scanning Tool for Developer Pipelines


## Abstract

Security Gatekeeper is a local-first security scanning tool that orchestrates three industry-standard scanners — Semgrep, Trivy, and Bandit — in parallel, normalizes their findings into a unified schema, and applies a configurable policy engine to produce actionable, developer-friendly reports. The tool integrates natively as a Git pre-commit hook and in CI/CD pipelines, blocking commits or builds when configured policy thresholds are exceeded. This report describes the design decisions, implementation trade-offs, and a structured evaluation of the tool against known-vulnerable codebases, measuring precision, false-positive rate, and integration overhead.

---

## 1. Introduction

Security vulnerabilities are consistently introduced during development, not discovered at deployment. Despite the availability of mature static analysis tools such as Semgrep [1], Trivy [2], and Bandit [3], adoption among development teams remains low due to fragmented tooling, inconsistent output formats, and the absence of clear, team-wide policy enforcement. A developer running three separate scanners with three different output formats and no agreed standard for what constitutes a blocking issue is unlikely to act on any of them.

The core problem is not the absence of scanners — it is the absence of a unified, opinionated layer that turns scanner output into developer decisions. Tools like Snyk [4] and GitHub Advanced Security [5] address this commercially, but their output is locked into hosted platforms and opaque policy engines.

Security Gatekeeper addresses this gap with three design goals:

1. **Unification**: All scanner findings are normalized to a single `Finding` schema, enabling consistent policy evaluation regardless of the scanner that produced them.
2. **Configurability**: Policy rules are expressed in plain YAML, allowing teams to define their own blocking thresholds without code changes.
3. **Developer experience**: The tool integrates into the developer's existing workflow via pre-commit hooks and CI/CD, with exit codes and terminal output designed for fast feedback loops.

The result is a tool a small team can ship to their repository in minutes and immediately begin blocking real vulnerabilities from reaching code review.

---

## 2. Related Work

**Semgrep** is a pattern-based SAST engine that supports dozens of languages. It is fast, configurable, and has a large open-source rule registry. However, it produces only code-level findings and does not cover dependency vulnerabilities.

**Trivy** is a comprehensive vulnerability scanner from Aqua Security, covering container images, filesystems, and IaC. It is excellent at dependency CVE detection but does not perform code-level analysis.

**Bandit** is a Python-specific SAST tool that detects insecure coding patterns. It is deeply Python-aware but limited to a single language and does not cover dependencies.

**Pre-commit** is a framework for managing Git hooks, widely adopted in Python projects. It enables tools to run automatically before each commit, but does not provide any policy evaluation or unified reporting.

None of the above tools alone covers the full attack surface of a modern software project. Security Gatekeeper is positioned as the orchestration and policy layer that makes these tools usable together.

---

## 3. System Design

### 3.1 Architecture

The system follows a linear pipeline architecture with a single extension point at the scanner layer:

```
CLI (Click)
    └── Config Loader (YAML)
            └── Scanner Orchestrator
                    ├── SemgrepScanner  ─┐
                    ├── TrivyScanner    ─┼── ThreadPoolExecutor (parallel)
                    └── BanditScanner   ─┘
            └── Normalizer (dedup + sort)
            └── Policy Engine (first-match wins)
            └── Terminal Reporter (Rich)
```

**CLI** (`cli.py`): Built with Click. Accepts `--target`, `--config`, and `--format` flags. Exits with code `1` if any finding is blocked, enabling pipeline integration without additional configuration.

**Config** (`config.py`): Loads `gatekeeper.yaml` and falls back to hardcoded defaults if the file is absent. This ensures the tool is usable out of the box.

**Scanner Orchestrator** (`scanner/__init__.py`): Dispatches all enabled scanners concurrently via `ThreadPoolExecutor`. Each scanner implements the `BaseScanner` abstract class, which enforces a 120-second execution timeout, respects `.gitignore` via `git ls-files`, and checks binary availability with `shutil.which()` before execution.

**Policy Engine** (`policy/engine.py`): Implements first-match-wins evaluation over an ordered list of rules. Rules are expressed as Python callables (or compiled from YAML) that take a `Finding` and return a `Decision` or `None`. The first rule to return a non-`None` value wins; if no rule matches, the configured `default_action` applies.

**Reporter** (`reporter/terminal.py`): Uses the Rich library to produce a color-coded table of blocked and warned findings, followed by a summary line indicating the overall scan result.

### 3.2 The Finding Schema

The central design decision is the `Finding` dataclass:

```python
@dataclass
class Finding:
    id: str
    scanner: str
    severity: Severity       # CRITICAL / HIGH /MEDIUM / LOW / INFO
    confidence: Confidence   # HIGH / MEDIUM / LOW
    cwe: str | None          # e.g. "CWE-89"
    category: Category       # sast / sca / iac / secrets
    title: str
    description: str
    file: str | None
    line: int | None
    rule_id: str
    extra: dict              # scanner-specific metadata
```

Choosing a common schema forces each scanner adapter to perform explicit mapping — a cost paid once at integration time in exchange for uniform downstream processing. The `cwe` field is particularly important: it enables policy rules to reason about vulnerability classes rather than scanner-specific rule names.

### 3.3 Deduplication

Semgrep and Bandit can both flag the same line for the same vulnerability class. The normalizer deduplicates findings by `(file, line)` key, keeping the highest-severity finding when a collision occurs. Findings without a file/line (typically Trivy's ecosystem-level vulnerability reports) are preserved separately.

### 3.4 Policy Engine Design

The default policy encodes six ordered rules:

| Priority | Condition | Decision |
|---|---|---|
| 1 | severity = CRITICAL | BLOCK |
| 2 | severity = HIGH ∧ cwe ∈ {CWE-78, CWE-89, CWE-94, CWE-79} | BLOCK |
| 3 | severity = HIGH ∧ cwe ∈ {CWE-502, CWE-798} | BLOCK |
| 4 | confidence = HIGH ∧ severity ∈ {HIGH, MEDIUM, CRITICAL} | BLOCK |
| 5 | severity = MEDIUM | WARN |
| 6 | severity ∈ {LOW, INFO} | ALLOW |

Rules 2 and 3 encode security domain knowledge: injection-family CWEs (SQL injection, command injection, XSS, code injection) and dangerous patterns (insecure deserialization, hardcoded credentials) are blocked regardless of confidence. Rule 4 acts as a backstop: any medium-or-higher finding that a scanner reports with high confidence is blocked even if it does not fall into a specific CWE class.

Teams can replace or extend these rules in `gatekeeper.yaml` without touching the codebase. A team that considers CWE-89 acceptable in a particular context can remove rule 2; a team with stricter requirements can add a rule that blocks all HIGH findings unconditionally.

---

## 4. Implementation

### 4.1 Scanner Adapters

Each adapter wraps a subprocess call to the scanner binary, parses the JSON output, and maps fields to the `Finding` schema. Key implementation details:

- **Semgrep**: Runs with `--json` output. Maps `ERROR → HIGH`, `WARNING → MEDIUM`, `INFO → LOW`. Extracts CWE from Semgrep's `metadata` block when available.
- **Trivy**: Runs in `fs` mode with `--format json`. Each CVE result produces a Finding; `pkg_name`, `installed_version`, and `fixed_version` are stored in `extra` for remediation guidance.
- **Bandit**: Runs with `-f json`. Maps Bandit's `SEVERITY` and `CONFIDENCE` directly. Bandit's output already includes CWE identifiers in newer versions.

### 4.2 Severity Comparison

`Severity` and `Confidence` are implemented as `StrEnum` with custom comparison operators (`__lt__`, `__gt__`, etc.), enabling natural comparisons like `Severity.HIGH > Severity.MEDIUM`. This allows the deduplicator to select the most severe finding without case analysis.

### 4.3 Pipeline Integration

**Pre-commit**: A `.pre-commit-hooks.yaml` file declares the hook, enabling any repository to add Security Gatekeeper with two lines in `.pre-commit-config.yaml`. The hook runs `gatekeeper scan` on the staged files' directory.

**CI/CD**: The exit code contract (`0` for pass/warn, `1` for block) makes integration into any CI system trivial. A GitHub Actions step that runs `python gatekeeper.py scan --target .` will fail the job automatically on any blocked finding.

### 4.4 Testing

The test suite covers all major components in isolation:

- **Policy engine**: 20 parameterized tests covering each default rule, boundary conditions, and custom rule evaluation.
- **Normalization**: Tests for deduplication collision resolution (severity wins), sort order, and unlocated findings preservation.
- **Reporter**: Tests verifying that blocked, warned, and allowed findings produce the correct output structure.
- **Config**: Tests for YAML parsing, missing fields, and default fallback behavior.
- **CLI**: Integration tests using `CliRunner` with mocked scanner output.

All scanner tests use fixture-based `Finding` objects rather than invoking real scanner binaries, keeping the suite fast and environment-independent.

---

## 5. Evaluation

### 5.1 Methodology

To evaluate the tool, we ran Security Gatekeeper against two codebases with known ground truth:

1. **dvpwa** (Damn Vulnerable Python Web Application) — a deliberately insecure aiohttp application containing documented instances of SQL injection, weak cryptography, and severely outdated dependencies with known CVEs.
2. **The project's own codebase** (`src/`) — to measure false positives on a clean, intentionally secure codebase.

For each BLOCKED finding on dvpwa, we manually classified it as a true positive (TP) or false positive (FP) by cross-referencing the CVE database and the dvpwa source code. We then computed precision and noise-reduction rate per scanner and overall.

### 5.2 Results

**Table 1 — Findings on dvpwa (vulnerable target)**

| Scanner | Raw findings | BLOCKED | WARNED | ALLOWED | Confirmed TP | FP | Precision |
|---|---|---|---|---|---|---|---|
| Semgrep | 2 | 0 | 0 | 2 | 0 | 0 | — |
| Trivy | 52 | 35 | 0 | 17 | 35 | 0 | 100% |
| Bandit | 1 | 1 | 0 | 0 | 1 | 0 | 100% |
| **Total** | **55** | **36** | **0** | **17** | **36** | **0** | **100%** |

All 36 BLOCKED findings were manually verified as true positives. Trivy identified 35 CVEs across three severely outdated packages (`aiohttp@3.5.3`, `pyyaml@3.13`, `jinja2@2.10`, `idna@2.8`). Bandit correctly identified MD5 usage in a security context (`sqli/dao/user.py:41`, CWE-327). Semgrep's 2 findings were LOW severity (correctly ALLOWED by policy). The 17 ALLOWED findings were low-severity Trivy CVEs where the policy correctly suppressed noise.

**Table 2 — Findings on clean project (`src/`) — false-positive baseline**

| Scanner | Raw findings | BLOCKED | WARNED | ALLOWED | FP rate (blocking) |
|---|---|---|---|---|---|
| Semgrep | 0 | 0 | 0 | 0 | 0% |
| Trivy | 0 | 0 | 0 | 0 | 0% |
| Bandit | 5 (4 after dedup) | 0 | 0 | 4 | 0% |
| **Total** | **5** | **0** | **0** | **4** | **0%** |

Bandit flagged 4 LOW/INFO findings in the tool's own source code (e.g., use of `subprocess`, which is expected and intentional in a scanner orchestrator). All were correctly classified as ALLOW by policy and did not surface in the terminal output as actionable items. Zero findings were incorrectly BLOCKED or WARNED on the clean codebase, giving a false-positive rate of 0% for both blocking and warning decisions.

**Table 3 — Scan execution time on dvpwa (Apple M1 2020, ~1200 LOC + requirements.txt)**

| Mode | Bandit | Trivy | Semgrep | Wall clock |
|---|---|---|---|---|
| Parallel (ThreadPoolExecutor) | 0.2s | 0.5s | 11.9s | **12.15s** |
| Sequential (estimated sum) | — | — | — | 12.6s |
| Speedup | | | | **1.04×** |

The modest speedup reflects that Semgrep dominates execution time at 11.9s. The 196% CPU usage observed during the run (via `time`) confirms that parallel execution was active — Trivy and Bandit completed in the background while Semgrep ran. In projects with more balanced scanner runtimes, or when scanning larger codebases where Trivy's dependency resolution takes longer, the parallelism benefit is more pronounced.

### 5.3 Policy Effectiveness

The policy engine's primary role is reducing noise. On dvpwa, 55 raw findings were reduced to 36 actionable BLOCKED items — a 34.5% noise reduction — with zero false positives. The 17 suppressed findings were all low-severity CVEs that do not represent an immediate exploitable risk, demonstrating that the ALLOW rule for LOW/INFO severity correctly filters non-critical alerts.

The absence of WARNED findings on dvpwa reflects the severity distribution of the target: all findings were either CRITICAL/HIGH (BLOCK) or LOW (ALLOW), with nothing in the MEDIUM range. In a more typical production codebase, WARN findings would serve as a review queue for developers.

### 5.4 Integration Overhead

The tool exits with code `1` when any finding is BLOCKED, enabling zero-configuration CI/CD integration. Adding it to a GitHub Actions workflow requires a single `run` step. For the pre-commit hook, integration requires adding two lines to `.pre-commit-config.yaml`. The total scan time of ~12s is acceptable for a pre-commit context on a small project, though larger monorepos may benefit from scoping the scan to changed files only.

---

## 6. Discussion

### 6.1 Design Trade-offs

**Parallel vs. sequential execution**: Running scanners concurrently reduces wall-clock time but means that scanner failures do not abort early. A Semgrep timeout will not prevent Trivy from completing. This is the correct trade-off for a developer tool: partial results are better than no results.

**Deduplication by (file, line)**: This strategy is conservative — two scanners detecting the same vulnerability class at different lines in the same function will produce two findings. A smarter deduplication using AST-level semantic equivalence was considered but rejected as over-engineering for the tool's scope.

**First-match wins vs. scoring**: An alternative policy engine design assigns numeric scores to findings (CVSS-style) and blocks above a threshold. First-match wins is simpler to reason about, easier for teams to configure, and produces more predictable results. Score-based systems can produce surprising outcomes when multiple rules partially match.

**No false-negative optimization**: The tool makes no attempt to enumerate all possible vulnerabilities in a target. It runs the scanners that are available and configured. This is deliberate: the tool's role is policy enforcement over scanner output, not comprehensive vulnerability discovery. Teams should select rulesets based on their threat model.

### 6.2 Limitations

- **Language coverage**: Bandit covers only Python. Teams working in Go, Java, or JavaScript rely entirely on Semgrep for code-level findings.
- **Context-blindness**: The policy engine operates on individual findings in isolation. It cannot express rules like "block if this file has more than 3 HIGH findings," which would require corpus-level reasoning.
- **Scanner availability**: The tool degrades gracefully when a scanner binary is absent, but provides no mechanism to install missing scanners. A `gatekeeper install` command would improve onboarding.
- **No secrets scanning**: The tool currently lacks a dedicated secrets scanner (e.g., Gitleaks, TruffleHog). Hardcoded credentials are partially covered by Bandit's CWE-798 rule, but detection recall is lower than a dedicated tool.

### 6.3 Future Work

The most impactful extensions would be:

1. **Secrets scanner integration**: Adding Gitleaks as a fourth scanner would cover a high-impact vulnerability class that all three current scanners handle weakly.
2. **Baseline mode**: Tracking findings across commits to surface only *new* findings, reducing noise for repositories with existing technical debt.
3. **SARIF output**: Producing SARIF-format reports would enable native integration with GitHub Code Scanning and other SARIF-aware platforms without custom adapters.

---

## 7. Conclusion

Security Gatekeeper demonstrates that a small, well-scoped tool can meaningfully shift security left in a development workflow. By treating scanner orchestration, finding normalization, and policy evaluation as three separable concerns with clean interfaces between them, the system remains extensible — adding a new scanner requires implementing a single abstract method, and changing enforcement policy requires editing a YAML file.

The tool solves a real problem: fragmented scanner output that developers ignore because it is noisy and provides no clear decision. By distilling three scanners' output into three decisions — BLOCK, WARN, ALLOW — Security Gatekeeper gives developers a clear answer: this commit can proceed, or it cannot, and here is exactly why.

---

## References

[1] R. Vemula et al., "Semgrep: Lightweight static analysis for many languages," *Semgrep Inc.*, 2020. https://semgrep.dev

[2] Aqua Security, "Trivy: Comprehensive security scanner," 2019. https://github.com/aquasecurity/trivy

[3] Python Software Foundation, "Bandit: A security linter for Python," *PyCQA*, 2014. https://github.com/PyCQA/bandit

[4] Snyk Ltd., "Snyk: Developer security platform," 2015. https://snyk.io

[5] GitHub Inc., "GitHub Advanced Security: Code scanning," 2020. https://docs.github.com/en/code-security
