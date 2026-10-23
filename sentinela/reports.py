"""Common, sanitized local report format and safe JSON export."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any

SCHEMA_VERSION = "1.0"
_REDACTED = "[REDACTED]"
_SENSITIVE_KEY = re.compile(
    r"(?:password|passwd|secret|token|api[_-]?key|authorization|cookie|session|private[_-]?key|credential)",
    re.IGNORECASE,
)
_SECRET_TEXT = re.compile(
    r"(?i)\b(bearer\s+)[A-Za-z0-9._~+/=-]+|"
    r"\b(password|passwd|secret|token|api[_-]?key|authorization|cookie)=([^\s&;,]+)"
)
_URL_SECRET = re.compile(
    r"(?i)([?&](?:password|passwd|secret|token|api[_-]?key|authorization|cookie)=)[^&#\s]+"
)


class ReportError(ValueError):
    """Raised when a report cannot be safely prepared or written."""


def sanitize(value: Any, *, key: str = "") -> Any:
    """Return JSON-safe data with sensitive fields and common secret strings redacted."""
    if _SENSITIVE_KEY.search(key):
        return _REDACTED
    if isinstance(value, dict):
        return {str(k): sanitize(v, key=str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize(item) for item in value]
    if isinstance(value, str):
        value = _URL_SECRET.sub(r"\1" + _REDACTED, value)
        value = _SECRET_TEXT.sub(
            lambda match: (match.group(1) + _REDACTED)
            if match.group(1) else (match.group(2) + "=" + _REDACTED),
            value,
        )
        return value
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)


def build_report(records: list[dict[str, Any]], *, source: str) -> dict[str, Any]:
    """Build the stable report envelope used by CLI output and JSON files."""
    if not isinstance(records, list) or any(not isinstance(item, dict) for item in records):
        raise ReportError("Os registros do relatório devem ser uma lista de objetos.")
    if not isinstance(source, str) or not source.strip():
        raise ReportError("A origem do relatório deve ser uma string não vazia.")
    cleaned = sanitize(records)
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "source": source.strip(),
        "record_count": len(cleaned),
        "results": cleaned,
    }


def export_json_report(
    records: list[dict[str, Any]],
    destination: str | Path,
    *,
    source: str,
    reports_dir: str | Path = "reports",
) -> Path:
    """Write a sanitized JSON report atomically, only inside the reports directory."""
    root = Path(reports_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    requested = Path(destination)
    target = (root / requested).resolve() if not requested.is_absolute() else requested.resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ReportError("O destino do relatório deve permanecer dentro do diretório reports.") from exc
    if target.suffix.lower() != ".json":
        raise ReportError("O arquivo de relatório deve usar a extensão .json.")
    report = build_report(records, source=source)
    try:
        serialized = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n",
            dir=target.parent, prefix=f".{target.name}.", suffix=".tmp", delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    except (OSError, TypeError, ValueError) as exc:
        try:
            if "temporary" in locals():
                temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise ReportError(f"Não foi possível gravar o relatório JSON: {exc}") from exc
    return target
