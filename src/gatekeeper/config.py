from pathlib import Path
from typing import Any

import yaml

_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "gatekeeper.yaml"


def load_config(config_path: str | None = None) -> dict[str, Any]:
    """Load gatekeeper configuration from a YAML file.

    Tries (in order): custom path from --config, then
    config/gatekeeper.yaml in the project root.
    Returns an empty dict if neither exists.
    """
    path = Path(config_path) if config_path else _DEFAULT_CONFIG_PATH

    if path.exists():
        with open(path) as fh:
            return yaml.safe_load(fh) or {}

    return {}
