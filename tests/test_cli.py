from sentinela.cli import build_parser, main


def test_cli_version_is_defined():
    parser = build_parser()
    assert parser.prog == "sentinela"


def test_cli_main_returns_success():
    assert main([]) == 0
