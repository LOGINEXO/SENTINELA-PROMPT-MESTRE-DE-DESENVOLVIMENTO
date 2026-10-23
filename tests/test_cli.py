import pytest

from sentinela.cli import build_parser, main


def test_cli_name_is_defined():
    assert build_parser().prog == "sentinela"


def test_cli_main_returns_success_without_network_activity():
    assert main([]) == 0


def test_cli_config_check_uses_example_by_default():
    args = build_parser().parse_args(["--check-config"])
    assert args.check_config == "config/settings.example.json"


def test_cli_rejects_unknown_arguments():
    with pytest.raises(SystemExit) as exc:
        main(["--not-a-real-option"])
    assert exc.value.code == 2
