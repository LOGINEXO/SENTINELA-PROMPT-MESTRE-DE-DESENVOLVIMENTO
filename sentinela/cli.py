"""Command-line entry point for the Sentinela foundation.

This stage performs local configuration validation only. It does not access
networks, scan assets, or start background jobs.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from sentinela import __version__
from sentinela.config import ConfigurationError, load_settings


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="sentinela",
        description=(
            "Fundação do Sentinela. Valida configurações locais; "
            "não executa varreduras nem requisições de rede."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--check-config",
        nargs="?",
        const="config/settings.example.json",
        metavar="PATH",
        help=(
            "valida um arquivo JSON de configuração local "
            "(padrão: config/settings.example.json)"
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, validate local configuration when requested."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.check_config:
        path = Path(args.check_config)
        try:
            load_settings(path)
        except ConfigurationError as exc:
            parser.error(str(exc))
        print(f"Configuração válida: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
