import json
import shutil
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

from src.gatekeeper.scanner.finding import Finding


class BaseScanner(ABC):
    """Interface that every scanner adapter must implement."""

    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def scan(self, target: Path) -> list[Finding]: ...

    def is_available(self) -> bool:
        """Check if the scanner binary is available in the system PATH."""
        return shutil.which(self.name()) is not None

    def _get_ignored_paths(self, target: Path) -> list[str]:
        """Returns a list of gitignored directories to exclude."""
        defaults = [".git", "__pycache__", ".tox", ".eggs", ".venv"]
        try:
            cwd = target if target.is_dir() else target.parent
            result = subprocess.run(
                ["git", "ls-files", "--others", "--ignored", "--exclude-standard", "--directory"],
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True
            )
            paths = [p.strip("/") for p in result.stdout.splitlines() if p]
            return list(set(paths + defaults))
        except (subprocess.CalledProcessError, FileNotFoundError):
            return defaults

    def _run_command(self, cmd: list[str], timeout: int = 120) -> dict:
        """Run a scanner command and return the parsed JSON output."""
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode not in (0, 1):
            raise RuntimeError(f"{self.name()} exited with code {result.returncode}: {result.stderr}")

        return json.loads(result.stdout) if result.stdout else {}
