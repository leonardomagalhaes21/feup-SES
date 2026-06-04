from __future__ import annotations

import textwrap

import pytest

from src.gatekeeper.config import load_config


def test_load_config_default_has_policy():
    config = load_config()

    assert "policy" in config
    assert "scanners" in config


def test_load_config_custom_path(tmp_path):
    config_path = tmp_path / "gatekeeper.yaml"
    config_path.write_text(
        textwrap.dedent(
            """
            policy:
              default_action: "ALLOW"
            scanners:
              semgrep:
                enabled: false
            """
        ).strip()
    )

    config = load_config(str(config_path))

    assert config["policy"]["default_action"] == "ALLOW"
    assert config["scanners"]["semgrep"]["enabled"] is False


def test_load_config_invalid_yaml(tmp_path):
    config_path = tmp_path / "gatekeeper.yaml"
    config_path.write_text("policy: [invalid")

    with pytest.raises(Exception):
        load_config(str(config_path))


def test_load_config_returns_empty_dict_when_path_does_not_exist(tmp_path):
    config = load_config(str(tmp_path / "nonexistent.yaml"))

    assert config == {}
