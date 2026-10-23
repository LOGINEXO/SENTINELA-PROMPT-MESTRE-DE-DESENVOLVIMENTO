"""Persistent task queue and PLAY/PAUSE/STOP controls for Sentinela."""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "reports" / "queue.sqlite3"
VALID_TASKS = {"nvd_search", "passive_audit"}
VALID_MODES = {"running", "paused", "stopped"}


class QueueError(ValueError):
    """Raised for invalid queue operations or task payloads."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def database_path() -> Path:
    configured = os.environ.get("SENTINELA_QUEUE_DB")
    path = Path(configured).expanduser() if configured else DEFAULT_DB
    if not path.is_absolute():
        path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def connect() -> sqlite3.Connection:
    db = sqlite3.connect(database_path(), timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA busy_timeout = 10000")
    db.execute("PRAGMA journal_mode = WAL")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS queue_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('queued','running','completed','failed','stopped')),
            created_at TEXT NOT NULL,
            started_at TEXT,
            finished_at TEXT,
            result_json TEXT,
            error TEXT
        );
        CREATE TABLE IF NOT EXISTS queue_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        INSERT OR IGNORE INTO queue_state(key, value) VALUES ('mode', 'running');
    """)
    return db


def _validate_payload(task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    if task_type not in VALID_TASKS:
        raise QueueError("Tipo de tarefa não permitido.")
    if not isinstance(payload, dict):
        raise QueueError("Payload de tarefa inválido.")
    if task_type == "nvd_search":
        query = payload.get("query")
        limit = payload.get("limit", 10)
        if not isinstance(query, str) or not query.strip() or len(query) > 120 or any(ord(c) < 32 or ord(c) == 127 for c in query):
            raise QueueError("A busca NVD exige palavra-chave válida de até 120 caracteres.")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise QueueError("O limite NVD deve estar entre 1 e 100.")
        return {"query": query.strip(), "limit": limit}
    host = payload.get("host")
    if not isinstance(host, str) or not host.strip() or len(host) > 253:
        raise QueueError("A auditoria exige um hostname válido.")
    # Validate syntax and exact allowlist at enqueue time; worker repeats this at execution time.
    from sentinela.scope import canonical_hostname, load_scope, require_in_scope
    canonical = canonical_hostname(host)
    scope_path = Path(os.environ.get("SENTINELA_SCOPE_FILE", ROOT / "config" / "authorized_targets.txt"))
    if not scope_path.is_absolute():
        scope_path = ROOT / scope_path
    allowed = load_scope(scope_path)
    require_in_scope(canonical, allowed)
    return {"host": canonical}


def enqueue(task_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    clean = _validate_payload(task_type, payload)
    with connect() as db:
        cursor = db.execute(
            "INSERT INTO queue_jobs(task_type,payload_json,status,created_at) VALUES(?,?,?,?)",
            (task_type, json.dumps(clean, ensure_ascii=False), "queued", utc_now()),
        )
        row = db.execute("SELECT * FROM queue_jobs WHERE id=?", (cursor.lastrowid,)).fetchone()
        return serialize_job(row)


def get_mode() -> str:
    with connect() as db:
        row = db.execute("SELECT value FROM queue_state WHERE key='mode'").fetchone()
        return str(row["value"]) if row else "stopped"


def set_mode(mode: str) -> dict[str, Any]:
    if mode not in VALID_MODES:
        raise QueueError("Controle inválido; use play, pause ou stop.")
    normalized = {"play": "running", "pause": "paused", "stop": "stopped"}.get(mode, mode)
    with connect() as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("INSERT INTO queue_state(key,value) VALUES('mode',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (normalized,))
        if normalized == "stopped":
            db.execute(
                "UPDATE queue_jobs SET status='stopped', finished_at=?, error='Cancelada pelo controle STOP antes da execução' WHERE status='queued'",
                (utc_now(),),
            )
        db.commit()
    return status()


def serialize_job(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["payload"] = json.loads(item.pop("payload_json"))
    if item.get("result_json"):
        if len(item["result_json"]) > 8000:
            item["result"] = {
                "truncated": True,
                "preview": item["result_json"][:8000],
                "note": "Resultado reduzido para exibição no histórico; o relatório completo permanece no banco local."
            }
        else:
            try:
                item["result"] = json.loads(item["result_json"])
            except json.JSONDecodeError:
                item["result"] = item["result_json"]
    item.pop("result_json", None)
    return item


def status(*, limit: int = 50) -> dict[str, Any]:
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 200:
        raise QueueError("O limite de histórico deve estar entre 1 e 200.")
    with connect() as db:
        mode_row = db.execute("SELECT value FROM queue_state WHERE key='mode'").fetchone()
        counts = {row["status"]: row["count"] for row in db.execute(
            "SELECT status, COUNT(*) AS count FROM queue_jobs GROUP BY status"
        )}
        rows = db.execute("SELECT * FROM queue_jobs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return {
        "mode": mode_row["value"] if mode_row else "stopped",
        "counts": {key: int(counts.get(key, 0)) for key in ("queued", "running", "completed", "failed", "stopped")},
        "jobs": [serialize_job(row) for row in rows],
    }


def claim_next() -> dict[str, Any] | None:
    with connect() as db:
        db.execute("BEGIN IMMEDIATE")
        mode_row = db.execute("SELECT value FROM queue_state WHERE key='mode'").fetchone()
        if not mode_row or mode_row["value"] != "running":
            db.commit()
            return None
        row = db.execute("SELECT id FROM queue_jobs WHERE status='queued' ORDER BY id LIMIT 1").fetchone()
        if row is None:
            db.commit()
            return None
        now = utc_now()
        db.execute("UPDATE queue_jobs SET status='running', started_at=? WHERE id=? AND status='queued'", (now, row["id"]))
        claimed = db.execute("SELECT * FROM queue_jobs WHERE id=?", (row["id"],)).fetchone()
        db.commit()
        return serialize_job(claimed)


def finish(job_id: int, *, result: Any = None, error: str | None = None) -> None:
    with connect() as db:
        db.execute("BEGIN IMMEDIATE")
        mode_row = db.execute("SELECT value FROM queue_state WHERE key='mode'").fetchone()
        mode = mode_row["value"] if mode_row else "stopped"
        if mode == "stopped":
            final_status = "stopped"
            final_error = error or "Execução concluída após solicitação de STOP."
        elif error is not None:
            final_status = "failed"
            final_error = error[:2000]
        else:
            final_status = "completed"
            final_error = None
        encoded = json.dumps(result, ensure_ascii=False, allow_nan=False) if result is not None else None
        db.execute(
            "UPDATE queue_jobs SET status=?, finished_at=?, result_json=?, error=? WHERE id=? AND status='running'",
            (final_status, utc_now(), encoded, final_error, job_id),
        )
        db.commit()
