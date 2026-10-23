"""Command-line interface to enqueue jobs and control the worker queue."""
from __future__ import annotations

import argparse
import json
import sys

from sentinela.queue import QueueError, enqueue, set_mode, status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gerencia a fila do Sentinela.")
    sub = parser.add_subparsers(dest="command", required=True)
    nvd = sub.add_parser("add-nvd", help="adiciona consulta NVD à fila")
    nvd.add_argument("--query", required=True)
    nvd.add_argument("--limit", type=int, default=10)
    audit = sub.add_parser("add-audit", help="adiciona auditoria passiva autorizada à fila")
    audit.add_argument("--host", required=True)
    active = sub.add_parser("add-active-audit", help="adiciona verificação ativa HTTPS limitada; requer escopo separado")
    active.add_argument("--host", required=True)
    active.add_argument("--confirm-authorized", action="store_true",
                        help="confirma que existe autorização documentada para este teste")
    control = sub.add_parser("control", help="controla a fila")
    control.add_argument("mode", choices=("play", "pause", "stop"))
    show = sub.add_parser("status", help="exibe status e histórico")
    show.add_argument("--limit", type=int, default=50)
    args = parser.parse_args(argv)
    try:
        if args.command == "add-nvd":
            output = enqueue("nvd_search", {"query": args.query, "limit": args.limit})
        elif args.command == "add-audit":
            output = enqueue("passive_audit", {"host": args.host})
        elif args.command == "add-active-audit":
            if not args.confirm_authorized:
                raise QueueError("Use --confirm-authorized somente após confirmar autorização documentada.")
            output = enqueue("active_audit", {"host": args.host, "confirm_authorized": True})
        elif args.command == "control":
            output = set_mode(args.mode)
        else:
            output = status(limit=args.limit)
    except (QueueError, ValueError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
