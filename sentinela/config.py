"""Load and validate local Sentinela JSON settings without side effects."""
from __future__ import annotations

import json
from math import isfinite
from pathlib import Path
from typing import Any


class ConfigurationError(ValueError):
    """Raised when a local settings file is unreadable or invalid."""


def load_settings(path: str | Path) -> dict[str, Any]:
    """Read and validate a settings JSON file; never perform network I/O."""
    settings_path = Path(path)
    try:
        with settings_path.open("r", encoding="utf-8") as settings_file:
            settings = json.load(settings_file)
    except OSError as exc:
        raise ConfigurationError(
            f"Não foi possível ler o arquivo de configuração: {settings_path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ConfigurationError(
            f"JSON inválido no arquivo {settings_path}, linha {exc.lineno}, "
            f"coluna {exc.colno}"
        ) from exc

    if not isinstance(settings, dict):
        raise ConfigurationError("A configuração raiz deve ser um objeto JSON.")

    _require_nonempty_string(settings, "environment")
    log_level = settings.get("log_level")
    allowed_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if not isinstance(log_level, str) or log_level not in allowed_levels:
        raise ConfigurationError(
            "log_level deve ser DEBUG, INFO, WARNING, ERROR ou CRITICAL."
        )
    _require_nonempty_string(settings, "reports_dir")

    network = settings.get("network")
    if not isinstance(network, dict):
        raise ConfigurationError("network deve ser um objeto.")
    if not isinstance(network.get("enabled"), bool):
        raise ConfigurationError("network.enabled deve ser booleano.")
    _require_positive_number(network, "timeout_seconds")
    _require_positive_integer(network, "max_concurrency")
    _require_positive_integer(network, "max_requests_per_run")

    authorization = settings.get("authorization")
    if not isinstance(authorization, dict):
        raise ConfigurationError("authorization deve ser um objeto.")
    if authorization.get("required_for_active_checks") is not True:
        raise ConfigurationError(
            "authorization.required_for_active_checks deve permanecer true."
        )
    _require_nonempty_string(authorization, "targets_file")

    return settings


def _require_nonempty_string(values: dict[str, Any], key: str) -> None:
    value = values.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"{key} deve ser uma string não vazia.")


def _require_positive_integer(values: dict[str, Any], key: str) -> None:
    value = values.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ConfigurationError(f"{key} deve ser um inteiro positivo.")


def _require_positive_number(values: dict[str, Any], key: str) -> None:
    value = values.get(key)
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not isfinite(value)
        or value <= 0
    ):
        raise ConfigurationError(f"{key} deve ser um número positivo.")
