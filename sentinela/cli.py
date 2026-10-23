"""Command-line entry point for the Sentinela foundation and public intelligence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from sentinela import __version__
from sentinela.config import ConfigurationError, load_settings
from sentinela.intelligence.nvd import NVDClientError, get_cve, search_cves


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="sentinela",
        description="Sentinela: valida configuração local e consulta inteligência pública NVD/CVE.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--check-config", nargs="?", const="config/settings.example.json", metavar="PATH",
        help="valida um arquivo JSON de configuração local (padrão: config/settings.example.json)",
    )
    intel = parser.add_mutually_exclusive_group()
    intel.add_argument("--nvd-search", metavar="KEYWORD", help="consulta CVEs públicos na NVD por palavra-chave")
    intel.add_argument("--nvd-cve", metavar="CVE-ID", help="consulta um CVE específico na NVD")
    parser.add_argument("--limit", type=int, default=20, help="máximo de resultados NVD (1-100; padrão: 20)")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run local validation or an explicitly requested public NVD query."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.check_config:
        path = Path(args.check_config)
        try:
            load_settings(path)
        except ConfigurationError as exc:
            parser.error(str(exc))
        print(f"Configuração válida: {path}")
    if args.nvd_search is not None or args.nvd_cve is not None:
        try:
            if args.nvd_search is not None:
                records = search_cves(args.nvd_search, limit=args.limit)
            else:
                if args.limit != 20:
                    parser.error("--limit só pode ser usado com --nvd-search; --nvd-cve retorna um registro.")
                record = get_cve(args.nvd_cve)
                records = [record] if record else []
        except (NVDClientError, ValueError) as exc:
            parser.error(str(exc))
        print(json.dumps(records, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
