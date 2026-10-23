import json
from pathlib import Path

import pytest

from sentinela.config import ConfigurationError, load_settings


ROOT = Path(__file__).resolve().parents[1]


def test_example_configuration_is_valid():
    settings = load_settings(ROOT / "config" / "settings.example.json")
    assert settings["network"]["enabled"] is False
    assert settings["authorization"]["required_for_active_checks"] is True


def test_missing_configuration_fails_clearly(tmp_path):
    with pytest.raises(ConfigurationError, match="Não foi possível ler"):
        load_settings(tmp_path / "missing.json")


def test_invalid_json_is_rejected(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{not-json", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="JSON inválido"):
        load_settings(path)


def test_non_positive_request_limit_is_rejected(tmp_path):
    source = ROOT / "config" / "settings.example.json"
    settings = json.loads(source.read_text(encoding="utf-8"))
    settings["network"]["max_requests_per_run"] = 0
    path = tmp_path / "settings.json"
    path.write_text(json.dumps(settings), encoding="utf-8")
    with pytest.raises(ConfigurationError, match="max_requests_per_run"):
        load_settings(path)


def test_non_finite_timeout_is_rejected(tmp_path):
    source = ROOT / "config" / "settings.example.json"
    settings = json.loads(source.read_text(encoding="utf-8"))
    settings["network"]["timeout_seconds"] = float("nan")
    path = tmp_path / "settings.json"
    path.write_text(json.dumps(settings), encoding="utf-8")
    with pytest.raises(ConfigurationError, match="timeout_seconds"):
        load_settings(path)


def test_disabling_authorization_for_active_checks_is_rejected(tmp_path):
    source = ROOT / "config" / "settings.example.json"
    settings = json.loads(source.read_text(encoding="utf-8"))
    settings["authorization"]["required_for_active_checks"] = False
    path = tmp_path / "settings.json"
    path.write_text(json.dumps(settings), encoding="utf-8")
    with pytest.raises(ConfigurationError, match="deve permanecer true"):
        load_settings(path)
