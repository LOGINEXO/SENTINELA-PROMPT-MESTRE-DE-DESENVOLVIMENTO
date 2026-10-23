"""Worker process for queued Sentinela jobs."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from sentinela.queue import ROOT, claim_next, finish, get_mode
from sentinela.intelligence.nvd import search_cves
from sentinela.reports import build_report
from sentinela.scope import load_scope
from sentinela.audit.passive import audit_https
from sentinela.audit.active import audit_https_get


def execute(job: dict) -> dict:
    payload = job["payload"]
    if job["task_type"] == "nvd_search":
        records = search_cves(payload["query"], limit=payload["limit"])
        return build_report(records, source="NVD")
    if job["task_type"] == "passive_audit":
        scope_path = Path(__import__("os").environ.get("SENTINELA_SCOPE_FILE", ROOT / "config" / "authorized_targets.txt"))
        if not scope_path.is_absolute():
            scope_path = ROOT / scope_path
        allowed_hosts = load_scope(scope_path)
        result = audit_https(payload["host"], allowed_hosts=allowed_hosts)
        return build_report([result], source="passive-https-audit")
    if job["task_type"] == "active_audit":
        if payload.get("confirm_authorized") is not True:
            raise ValueError("Confirmação explícita de autorização ausente.")
        scope_path = Path(__import__("os").environ.get("SENTINELA_ACTIVE_SCOPE_FILE", ROOT / "config" / "authorized_active_targets.txt"))
        if not scope_path.is_absolute():
            scope_path = ROOT / scope_path
        allowed_hosts = load_scope(scope_path)
        result = audit_https_get(payload["host"], allowed_hosts=allowed_hosts)
        return build_report([result], source="authorized-active-https-check")
    raise ValueError("Tipo de tarefa não permitido.")


def run_worker(*, poll_interval: float = 0.5, once: bool = False) -> int:
    if not 0.1 <= poll_interval <= 5:
        raise ValueError("poll_interval deve ficar entre 0,1 e 5 segundos.")
    while True:
        job = claim_next()
        if job is None:
            if once:
                return 0
            time.sleep(poll_interval)
            continue
        try:
            result = execute(job)
            finish(job["id"], result=result)
        except Exception as exc:
            # Persist a concise error, not a traceback or environment details.
            finish(job["id"], error=f"{type(exc).__name__}: {str(exc)[:1800]}")
        if once:
            return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Worker da fila Sentinela.")
    parser.add_argument("--poll-interval", type=float, default=0.5, help="intervalo de espera em segundos (0,1–5)")
    parser.add_argument("--once", action="store_true", help="processa no máximo uma tarefa e encerra")
    args = parser.parse_args(argv)
    try:
        return run_worker(poll_interval=args.poll_interval, once=args.once)
    except ValueError as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
