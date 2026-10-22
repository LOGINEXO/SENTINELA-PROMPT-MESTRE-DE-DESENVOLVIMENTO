"""Minimal CLI for the Sentinela foundation; no network activity is performed."""

from __future__ import annotations

import argparse

from sentinela import __version__


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="sentinela",
        description=(
            "Fundação do Sentinela. Nesta etapa, o CLI apenas apresenta "
            "informações e não executa varreduras nem requisições de rede."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and return a process exit code."""
    build_parser().parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
