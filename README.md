# Security Gatekeeper

A local-first security gatekeeper that catches vulnerabilities **before they reach your pipeline**.

Runs [Semgrep](https://semgrep.dev/) (SAST), [Trivy](https://trivy.dev/) (dependency scanning), and [Bandit](https://bandit.readthedocs.io/) (Python SAST) -- then applies a **Python policy engine** to block, warn, or allow findings.

## Features

- **Instant scanning** -- runs on demand or via pre-commit hook
- **3 scanners** -- Semgrep, Trivy, Bandit with unified JSON output
- **Python policy engine** -- 6 configurable rules (block / warn / allow)
- **Rich terminal reports** -- colour-coded, readable output
- **Pre-commit hook** -- blocks bad commits automatically


## Prerequisites

You need the following installed on your machine before setting up the project:

| Tool | Purpose | Install |
|------|---------|---------|
| **Python 3.14+** | Runtime | [python.org](https://www.python.org/downloads/) or `brew install python@3.14` |
| **uv** | Python package manager | `curl -LsSf https://astral.sh/uv/install.sh \| sh` or `brew install uv` |
| **Semgrep** | Static analysis (SAST) | `pip install semgrep` or `brew install semgrep` |
| **Trivy** | Dependency vulnerability scanner | `brew install trivy` or [see docs](https://trivy.dev/docs/latest/guide/) |

Bandit is installed automatically as a Python dependency -- no separate install needed.

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-user/feup-SES.git
cd feup-SES

# 2. Install Python dependencies (creates .venv automatically)
uv sync

# 3. (Optional) Place a target application to scan in the target/ directory
#    For example, clone a vulnerable app:
#    git clone https://github.com/adeyosemanputra/pygoat.git target/pygoat
```

After `uv sync`, all Python dependencies (click, rich, pyyaml, bandit, semgrep) are installed
in a local `.venv` virtual environment.

## Usage

### Scanning a project

```bash
# Scan the target/ directory (or any path)
python gatekeeper.py scan --target ./target

# Scan a specific project with a custom config
python gatekeeper.py scan --target ./myapp --config config/gatekeeper.yaml
```

The scan command will:
1. Run all enabled scanners (Semgrep, Trivy, Bandit) against the target
2. Normalize findings into a unified format
3. Evaluate each finding against the policy rules
4. Print a colour-coded report to the terminal
5. Exit with code 1 if any finding is BLOCKED, 0 otherwise

### Pre-commit hook (Native Integration)

The tool can be wired into git using the standard `pre-commit` framework so it runs automatically on every commit.

In any project where you want to use Security Gatekeeper, simply add the following to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/leonardomagalhaes21/feup-SES
    rev: main
    hooks:
      - id: gatekeeper
        # Optional: override default target or pass config
        args: ["--target", ".", "--config", "gatekeeper.yaml"]
```

By default, the hook scans the current directory (`--target .`). You can override this or pass a custom config using `args`.

Then install it using:
```bash
pre-commit install
```

Every `git commit` will now trigger a scan first. If any finding is BLOCKED, the commit is rejected.

### Example output

```

  [scan] Running 3 scanner(s) in parallel...
  [done] trivy -- 127 finding(s) in 0.1s
  [done] bandit -- 60 finding(s) in 0.2s
  [done] semgrep -- 0 finding(s) in 2.1s

───────────────────────────────────────────────────────────────────────────────────── 🔍 Security Gatekeeper | Scan Results ─────────────────────────────────────────────────────────────────────────────────────

┏━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃     ┃ Decision   ┃ CWE        ┃ Location                                                     ┃ Description                                                                                                    ┃
┡━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ ❌  │ BLOCKED    │ CWE-79     │ pygoat/dockerized_labs/broken_auth_lab/requirements.txt      │ Jinja2@3.1.2 -> CVE-2024-22195                                                                                 │
│ ❌  │ BLOCKED    │ CWE-79     │ pygoat/dockerized_labs/broken_auth_lab/requirements.txt      │ Jinja2@3.1.2 -> CVE-2024-34064                                                                                 │
│ ❌  │ BLOCKED    │ CWE-150    │ pygoat/dockerized_labs/broken_auth_lab/requirements.txt      │ Jinja2@3.1.2 -> CVE-2024-56201                                                                                 │
│ ❌  │ BLOCKED    │ CWE-693    │ pygoat/dockerized_labs/broken_auth_lab/requirements.txt      │ Jinja2@3.1.2 -> CVE-2024-56326                                                                                 │
│ ❌  │ BLOCKED    │ CWE-1336   │ pygoat/dockerized_labs/broken_auth_lab/requirements.txt      │ Jinja2@3.1.2 -> CVE-2025-27516                                                                                 │
│ ❌  │ BLOCKED    │ CWE-352    │ pygoat/dockerized_labs/broken_auth_lab/requirements.txt      │ Werkzeug@2.3.7 -> CVE-2024-34069                                                                               │
│ ❌  │ BLOCKED    │ CWE-400    │ pygoat/dockerized_labs/broken_auth_lab/requirements.txt      │ Werkzeug@2.3.7 -> CVE-2023-46136                                                                               │
│ ❌  │ BLOCKED    │ CWE-22     │ pygoat/dockerized_labs/broken_auth_lab/requirements.txt      │ Werkzeug@2.3.7 -> CVE-2024-49766                                                                               │
│ ❌  │ BLOCKED    │ CWE-400    │ pygoat/dockerized_labs/broken_auth_lab/requirements.txt      │ Werkzeug@2.3.7 -> CVE-2024-49767                                                                               │
│ ❌  │ BLOCKED    │ CWE-67     │ pygoat/dockerized_labs/broken_auth_lab/requirements.txt      │ Werkzeug@2.3.7 -> CVE-2025-66221                                                                               │
│ ❌  │ BLOCKED    │ CWE-67     │ pygoat/dockerized_labs/broken_auth_lab/requirements.txt      │ Werkzeug@2.3.7 -> CVE-2026-21860                                                                               │
│ ❌  │ BLOCKED    │ CWE-67     │ pygoat/dockerized_labs/broken_auth_lab/requirements.txt      │ Werkzeug@2.3.7 -> CVE-2026-27199                                                                               │
│ ❌  │ BLOCKED    │ CWE-352    │ pygoat/dockerized_labs/insec_des_lab/requirements.txt        │ Werkzeug@3.0.1 -> CVE-2024-34069                                                                               │
│ ❌  │ BLOCKED    │ CWE-22     │ pygoat/dockerized_labs/insec_des_lab/requirements.txt        │ Werkzeug@3.0.1 -> CVE-2024-49766                                                                               │
│ ❌  │ BLOCKED    │ CWE-400    │ pygoat/dockerized_labs/insec_des_lab/requirements.txt        │ Werkzeug@3.0.1 -> CVE-2024-49767                                                                               │
│ ❌  │ BLOCKED    │ CWE-67     │ pygoat/dockerized_labs/insec_des_lab/requirements.txt        │ Werkzeug@3.0.1 -> CVE-2025-66221                                                                               │
│ ❌  │ BLOCKED    │ CWE-67     │ pygoat/dockerized_labs/insec_des_lab/requirements.txt        │ Werkzeug@3.0.1 -> CVE-2026-21860                                                                               │
│ ❌  │ BLOCKED    │ CWE-67     │ pygoat/dockerized_labs/insec_des_lab/requirements.txt        │ Werkzeug@3.0.1 -> CVE-2026-27199                                                                               │
│ ❌  │ BLOCKED    │ CWE-20     │ pygoat/dockerized_labs/sensitive_data_exposure/requirements… │ django@3.2.18 -> CVE-2023-31047                                                                                │
│ ❌  │ BLOCKED    │ CWE-89     │ pygoat/dockerized_labs/sensitive_data_exposure/requirements… │ django@3.2.18 -> CVE-2025-64459                                                                                │
│ ❌  │ BLOCKED    │ CWE-1333   │ pygoat/dockerized_labs/sensitive_data_exposure/requirements… │ django@3.2.18 -> CVE-2023-36053                                                                                │
│ ❌  │ BLOCKED    │ CWE-1284   │ pygoat/dockerized_labs/sensitive_data_exposure/requirements… │ django@3.2.18 -> CVE-2023-43665                                                                                │
│ ❌  │ BLOCKED    │ CWE-770    │ pygoat/dockerized_labs/sensitive_data_exposure/requirements… │ django@3.2.18 -> CVE-2023-46695                                                                                │
│ ❌  │ BLOCKED    │ —          │ pygoat/dockerized_labs/sensitive_data_exposure/requirements… │ django@3.2.18 -> CVE-2024-24680                                                                                │
│ ❌  │ BLOCKED    │ CWE-89     │ pygoat/dockerized_labs/sensitive_data_exposure/requirements… │ django@3.2.18 -> CVE-2025-57833                                                                                │
│ ❌  │ BLOCKED    │ CWE-407    │ pygoat/dockerized_labs/sensitive_data_exposure/requirements… │ django@3.2.18 -> CVE-2025-64458                                                                                │
│ ❌  │ BLOCKED    │ CWE-1284   │ pygoat/dockerized_labs/sensitive_data_exposure/requirements… │ django@3.2.18 -> CVE-2023-41164                                                                                │
│ ❌  │ BLOCKED    │ CWE-1333   │ pygoat/dockerized_labs/sensitive_data_exposure/requirements… │ django@3.2.18 -> CVE-2024-27351                                                                                │
│ ❌  │ BLOCKED    │ CWE-203    │ pygoat/dockerized_labs/sensitive_data_exposure/requirements… │ django@3.2.18 -> CVE-2024-45231                                                                                │
│ ❌  │ BLOCKED    │ CWE-117    │ pygoat/dockerized_labs/sensitive_data_exposure/requirements… │ django@3.2.18 -> CVE-2025-48432                                                                                │
│ ❌  │ BLOCKED    │ CWE-200    │ pygoat/dockerized_labs/sensitive_data_exposure/requirements… │ requests@2.28.1 -> CVE-2023-32681                                                                              │
│ ❌  │ BLOCKED    │ CWE-670    │ pygoat/dockerized_labs/sensitive_data_exposure/requirements… │ requests@2.28.1 -> CVE-2024-35195                                                                              │
│ ❌  │ BLOCKED    │ CWE-522    │ pygoat/dockerized_labs/sensitive_data_exposure/requirements… │ requests@2.28.1 -> CVE-2024-47081                                                                              │
│ ❌  │ BLOCKED    │ CWE-377    │ pygoat/dockerized_labs/sensitive_data_exposure/requirements… │ requests@2.28.1 -> CVE-2026-25645                                                                              │
│ ❌  │ BLOCKED    │ CWE-20     │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2023-31047                                                                                   │
│ ❌  │ BLOCKED    │ CWE-89     │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2024-42005                                                                                   │
│ ❌  │ BLOCKED    │ CWE-89     │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2025-64459                                                                                   │
│ ❌  │ BLOCKED    │ CWE-1333   │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2023-36053                                                                                   │
│ ❌  │ BLOCKED    │ CWE-1284   │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2023-43665                                                                                   │
│ ❌  │ BLOCKED    │ CWE-770    │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2023-46695                                                                                   │
│ ❌  │ BLOCKED    │ —          │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2024-24680                                                                                   │
│ ❌  │ BLOCKED    │ CWE-130    │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2024-38875                                                                                   │
│ ❌  │ BLOCKED    │ CWE-22     │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2024-39330                                                                                   │
│ ❌  │ BLOCKED    │ CWE-130    │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2024-39614                                                                                   │
│ ❌  │ BLOCKED    │ CWE-89     │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2024-53908                                                                                   │
│ ❌  │ BLOCKED    │ CWE-89     │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2025-57833                                                                                   │
│ ❌  │ BLOCKED    │ CWE-89     │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2025-59681                                                                                   │
│ ❌  │ BLOCKED    │ CWE-407    │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2025-64458                                                                                   │
│ ❌  │ BLOCKED    │ CWE-89     │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2026-1207                                                                                    │
│ ❌  │ BLOCKED    │ CWE-89     │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2026-1287                                                                                    │
│ ❌  │ BLOCKED    │ CWE-400    │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2026-25673                                                                                   │
│ ❌  │ BLOCKED    │ CWE-770    │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2026-33034                                                                                   │
│ ❌  │ BLOCKED    │ CWE-290    │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2026-3902                                                                                    │
│ ❌  │ BLOCKED    │ CWE-1284   │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2023-41164                                                                                   │
│ ❌  │ BLOCKED    │ CWE-1333   │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2024-27351                                                                                   │
│ ❌  │ BLOCKED    │ CWE-208    │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2024-39329                                                                                   │
│ ❌  │ BLOCKED    │ CWE-400    │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2024-41989                                                                                   │
│ ❌  │ BLOCKED    │ CWE-130    │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2024-41990                                                                                   │
│ ❌  │ BLOCKED    │ CWE-1284   │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2024-41991                                                                                   │
│ ❌  │ BLOCKED    │ CWE-120    │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2024-45230                                                                                   │
│ ❌  │ BLOCKED    │ CWE-203    │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2024-45231                                                                                   │
│ ❌  │ BLOCKED    │ CWE-770    │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2024-53907                                                                                   │
│ ❌  │ BLOCKED    │ CWE-770    │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2024-56374                                                                                   │
│ ❌  │ BLOCKED    │ CWE-89     │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2025-13372                                                                                   │
│ ❌  │ BLOCKED    │ CWE-770    │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2025-26699                                                                                   │
│ ❌  │ BLOCKED    │ CWE-770    │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2025-32873                                                                                   │
│ ❌  │ BLOCKED    │ CWE-117    │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2025-48432                                                                                   │
│ ❌  │ BLOCKED    │ CWE-407    │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2025-64460                                                                                   │
│ ❌  │ BLOCKED    │ CWE-89     │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2026-1312                                                                                    │
│ ❌  │ BLOCKED    │ CWE-407    │ pygoat/requirements.txt                                      │ Django@4.2 -> CVE-2026-33033                                                                                   │
│ ❌  │ BLOCKED    │ CWE-94     │ pygoat/requirements.txt                                      │ Pillow@9.4.0 -> CVE-2023-50447                                                                                 │
│ ❌  │ BLOCKED    │ CWE-770    │ pygoat/requirements.txt                                      │ Pillow@9.4.0 -> CVE-2023-44271                                                                                 │
│ ❌  │ BLOCKED    │ CWE-787    │ pygoat/requirements.txt                                      │ Pillow@9.4.0 -> CVE-2023-4863                                                                                  │
│ ❌  │ BLOCKED    │ CWE-680    │ pygoat/requirements.txt                                      │ Pillow@9.4.0 -> CVE-2024-28219                                                                                 │
│ ❌  │ BLOCKED    │ CWE-345    │ pygoat/requirements.txt                                      │ PyJWT@2.4.0 -> CVE-2026-32597                                                                                  │
│ ❌  │ BLOCKED    │ CWE-502    │ pygoat/requirements.txt                                      │ PyYAML@5.1 -> CVE-2019-20477                                                                                   │
│ ❌  │ BLOCKED    │ CWE-20     │ pygoat/requirements.txt                                      │ PyYAML@5.1 -> CVE-2020-14343                                                                                   │
│ ❌  │ BLOCKED    │ CWE-20     │ pygoat/requirements.txt                                      │ PyYAML@5.1 -> CVE-2020-1747                                                                                    │
│ ❌  │ BLOCKED    │ CWE-770    │ pygoat/requirements.txt                                      │ Werkzeug@2.1.2 -> CVE-2023-25577                                                                               │
│ ❌  │ BLOCKED    │ CWE-352    │ pygoat/requirements.txt                                      │ Werkzeug@2.1.2 -> CVE-2024-34069                                                                               │
│ ❌  │ BLOCKED    │ CWE-400    │ pygoat/requirements.txt                                      │ Werkzeug@2.1.2 -> CVE-2023-46136                                                                               │
│ ❌  │ BLOCKED    │ CWE-22     │ pygoat/requirements.txt                                      │ Werkzeug@2.1.2 -> CVE-2024-49766                                                                               │
│ ❌  │ BLOCKED    │ CWE-400    │ pygoat/requirements.txt                                      │ Werkzeug@2.1.2 -> CVE-2024-49767                                                                               │
│ ❌  │ BLOCKED    │ CWE-67     │ pygoat/requirements.txt                                      │ Werkzeug@2.1.2 -> CVE-2025-66221                                                                               │
│ ❌  │ BLOCKED    │ CWE-67     │ pygoat/requirements.txt                                      │ Werkzeug@2.1.2 -> CVE-2026-21860                                                                               │
│ ❌  │ BLOCKED    │ CWE-67     │ pygoat/requirements.txt                                      │ Werkzeug@2.1.2 -> CVE-2026-27199                                                                               │
│ ❌  │ BLOCKED    │ CWE-345    │ pygoat/requirements.txt                                      │ certifi@2022.12.7 -> CVE-2023-37920                                                                            │
│ ❌  │ BLOCKED    │ CWE-203    │ pygoat/requirements.txt                                      │ cryptography@39.0.1 -> CVE-2023-50782                                                                          │
│ ❌  │ BLOCKED    │ CWE-476    │ pygoat/requirements.txt                                      │ cryptography@39.0.1 -> CVE-2024-26130                                                                          │
│ ❌  │ BLOCKED    │ CWE-345    │ pygoat/requirements.txt                                      │ cryptography@39.0.1 -> CVE-2026-26007                                                                          │
│ ❌  │ BLOCKED    │ CWE-476    │ pygoat/requirements.txt                                      │ cryptography@39.0.1 -> CVE-2023-49083                                                                          │
│ ❌  │ BLOCKED    │ CWE-476    │ pygoat/requirements.txt                                      │ cryptography@39.0.1 -> CVE-2024-0727                                                                           │
│ ❌  │ BLOCKED    │ —          │ pygoat/requirements.txt                                      │ cryptography@39.0.1 -> GHSA-h4gh-qq45-vh27                                                                     │
│ ❌  │ BLOCKED    │ CWE-613    │ pygoat/requirements.txt                                      │ django-allauth@0.52.0 -> CVE-2025-65430                                                                        │
│ ❌  │ BLOCKED    │ CWE-287    │ pygoat/requirements.txt                                      │ django-allauth@0.52.0 -> CVE-2025-65431                                                                        │
│ ❌  │ BLOCKED    │ CWE-601    │ pygoat/requirements.txt                                      │ django-allauth@0.52.0 -> CVE-2026-27982                                                                        │
│ ❌  │ BLOCKED    │ CWE-1333   │ pygoat/requirements.txt                                      │ idna@3.4 -> CVE-2024-3651                                                                                      │
│ ❌  │ BLOCKED    │ CWE-200    │ pygoat/requirements.txt                                      │ requests@2.28.2 -> CVE-2023-32681                                                                              │
│ ❌  │ BLOCKED    │ CWE-670    │ pygoat/requirements.txt                                      │ requests@2.28.2 -> CVE-2024-35195                                                                              │
│ ❌  │ BLOCKED    │ CWE-522    │ pygoat/requirements.txt                                      │ requests@2.28.2 -> CVE-2024-47081                                                                              │
│ ❌  │ BLOCKED    │ CWE-377    │ pygoat/requirements.txt                                      │ requests@2.28.2 -> CVE-2026-25645                                                                              │
│ ❌  │ BLOCKED    │ CWE-674    │ pygoat/requirements.txt                                      │ sqlparse@0.3.1 -> CVE-2024-4340                                                                                │
│ ❌  │ BLOCKED    │ CWE-1333   │ pygoat/requirements.txt                                      │ sqlparse@0.3.1 -> CVE-2023-30608                                                                               │
│ ❌  │ BLOCKED    │ —          │ pygoat/requirements.txt                                      │ sqlparse@0.3.1 -> GHSA-27jp-wm6q-gp25                                                                          │
│ ❌  │ BLOCKED    │ CWE-200    │ pygoat/requirements.txt                                      │ urllib3@1.26.9 -> CVE-2023-43804                                                                               │
│ ❌  │ BLOCKED    │ CWE-770    │ pygoat/requirements.txt                                      │ urllib3@1.26.9 -> CVE-2025-66418                                                                               │
│ ❌  │ BLOCKED    │ CWE-409    │ pygoat/requirements.txt                                      │ urllib3@1.26.9 -> CVE-2025-66471                                                                               │
│ ❌  │ BLOCKED    │ CWE-409    │ pygoat/requirements.txt                                      │ urllib3@1.26.9 -> CVE-2026-21441                                                                               │
│ ❌  │ BLOCKED    │ CWE-200    │ pygoat/requirements.txt                                      │ urllib3@1.26.9 -> CVE-2023-45803                                                                               │
│ ❌  │ BLOCKED    │ CWE-669    │ pygoat/requirements.txt                                      │ urllib3@1.26.9 -> CVE-2024-37891                                                                               │
│ ❌  │ BLOCKED    │ CWE-601    │ pygoat/requirements.txt                                      │ urllib3@1.26.9 -> CVE-2025-50181                                                                               │
│ ❌  │ BLOCKED    │ CWE-835    │ pygoat/requirements.txt                                      │ zipp@3.8.0 -> CVE-2024-5569                                                                                    │
│ ❌  │ BLOCKED    │ CWE-327    │ pygoat/dockerized_labs/broken_auth_lab/app.py:86             │ Use of weak MD5 hash for security. Consider usedforsecurity=False                                              │
│ ❌  │ BLOCKED    │ CWE-94     │ pygoat/dockerized_labs/broken_auth_lab/app.py:123            │ A Flask app appears to be run with debug=True, which exposes the Werkzeug debugger and allows the execution of │
│     │            │            │                                                              │ arbitrary                                                                                                      │
│ ❌  │ BLOCKED    │ CWE-502    │ pygoat/dockerized_labs/insec_des_lab/main.py:36              │ Pickle and modules that wrap it can be unsafe when used to deserialize untrusted data, possible security       │
│     │            │            │                                                              │ issue.                                                                                                         │
│ ❌  │ BLOCKED    │ CWE-20     │ pygoat/introduction/lab_code/test.py:23                      │ Use of unsafe yaml load. Allows instantiation of arbitrary objects. Consider yaml.safe_load().                 │
│ ❌  │ BLOCKED    │ CWE-327    │ pygoat/introduction/mitre.py:161                             │ Use of weak MD5 hash for security. Consider usedforsecurity=False                                              │
│ ❌  │ BLOCKED    │ CWE-78     │ pygoat/introduction/mitre.py:218                             │ Use of possibly insecure function - consider using safer ast.literal_eval.                                     │
│ ❌  │ BLOCKED    │ CWE-78     │ pygoat/introduction/mitre.py:233                             │ subprocess call with shell=True identified, security issue.                                                    │
│ ❌  │ BLOCKED    │ CWE-502    │ pygoat/introduction/views.py:214                             │ Pickle and modules that wrap it can be unsafe when used to deserialize untrusted data, possible security       │
│     │            │            │                                                              │ issue.                                                                                                         │
│ ❌  │ BLOCKED    │ CWE-20     │ pygoat/introduction/views.py:258                             │ Using xml.sax.make_parser to parse untrusted XML data is known to be vulnerable to XML attacks. Replace        │
│     │            │            │                                                              │ xml.sax.make_par                                                                                               │
│ ❌  │ BLOCKED    │ CWE-20     │ pygoat/introduction/views.py:260                             │ Using xml.dom.pulldom.parseString to parse untrusted XML data is known to be vulnerable to XML attacks.        │
│     │            │            │                                                              │ Replace xml.dom.                                                                                               │
│ ❌  │ BLOCKED    │ CWE-78     │ pygoat/introduction/views.py:432                             │ subprocess call with shell=True identified, security issue.                                                    │
│ ❌  │ BLOCKED    │ CWE-78     │ pygoat/introduction/views.py:460                             │ Use of possibly insecure function - consider using safer ast.literal_eval.                                     │
│ ❌  │ BLOCKED    │ CWE-20     │ pygoat/introduction/views.py:560                             │ Use of unsafe yaml load. Allows instantiation of arbitrary objects. Consider yaml.safe_load().                 │
│ ❌  │ BLOCKED    │ CWE-327    │ pygoat/introduction/views.py:1026                            │ Use of weak MD5 hash for security. Consider usedforsecurity=False                                              │
│ ⚠️  │ WARNING    │ CWE-605    │ pygoat/dockerized_labs/broken_auth_lab/app.py:123            │ Possible binding to all interfaces.                                                                            │
│ ⚠️  │ WARNING    │ CWE-605    │ pygoat/dockerized_labs/insec_des_lab/main.py:51              │ Possible binding to all interfaces.                                                                            │
└─────┴────────────┴────────────┴──────────────────────────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

ℹ️  ALLOWED        59 finding(s): severity LOW/INFO, policy set to allow

Result: BLOCKED — fix 126 critical issue(s) before committing.
  Blocked: 126  |  Warnings: 2  |  Allowed: 59
```

## Configuration

Edit `config/gatekeeper.yaml` to enable/disable scanners and change the default policy action:

You can pass a custom config path with `--config`:

```bash
python gatekeeper.py scan --target ./myapp --config my-custom-config.yaml
```

## Policy Rules

The policy engine evaluates each finding against an ordered list of rules.
First match wins. If no rule matches, the `default_action` from the config is used.

Rules are defined as Python functions in `src/gatekeeper/policy/default_rules.py`.


## Makefile

Common commands are available via `make`:

```bash
make help      # Show all available commands
make install   # Install dependencies (uv sync)
make scan      # Scan ./target (default)
make scan TARGET=./myapp   # Scan a different path
make test      # Run unit tests
make pre-commit      # Install pre-commit hooks
```

## Running Tests

```bash
uv run pytest tests/ -v
```

## Pre-commit (Self-Scanning)

This project is configured to scan itself using its own rules. To activate the local pre-commit hook:

```bash
uv run pre-commit install
```

This will run the `gatekeeper-local` hook on every commit, ensuring that no vulnerabilities are introduced into the tool itself.
