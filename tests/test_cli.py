import json

import pytest

from sentinela.cli import build_parser, main
from sentinela.intelligence.nvd import NVDClientError


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


def test_nvd_search_prints_json_and_forwards_options(monkeypatch, capsys):
    captured = {}

    def fake_search(keyword, **kwargs):
        captured["keyword"] = keyword
        captured.update(kwargs)
        return [{"cve_id": "CVE-2025-12345", "asset_confirmed": False}]

    monkeypatch.setattr("sentinela.cli.search_cves", fake_search)
    assert main(["--nvd-search", " OpenSSH ", "--limit", "7",
                 "--modified-since", "2026-10-01T00:00:00Z"]) == 0
    assert captured == {
        "keyword": " OpenSSH ", "limit": 7,
        "modified_since": "2026-10-01T00:00:00Z", "modified_until": None,
    }
    assert json.loads(capsys.readouterr().out)[0]["cve_id"] == "CVE-2025-12345"


def test_nvd_cve_prints_single_record_as_json_array(monkeypatch, capsys):
    monkeypatch.setattr("sentinela.cli.get_cve", lambda cve_id: {"cve_id": cve_id})
    assert main(["--nvd-cve", "CVE-2025-12345"]) == 0
    assert json.loads(capsys.readouterr().out) == [{"cve_id": "CVE-2025-12345"}]


def test_nvd_cve_not_found_prints_empty_array(monkeypatch, capsys):
    monkeypatch.setattr("sentinela.cli.get_cve", lambda _cve_id: None)
    assert main(["--nvd-cve", "CVE-2025-12345"]) == 0
    assert json.loads(capsys.readouterr().out) == []


def test_nvd_errors_are_reported_as_cli_errors(monkeypatch):
    def fail(*_args, **_kwargs):
        raise NVDClientError("NVD indisponível")

    monkeypatch.setattr("sentinela.cli.search_cves", fail)
    with pytest.raises(SystemExit) as exc:
        main(["--nvd-search", "OpenSSH"])
    assert exc.value.code == 2


def test_incremental_options_require_search_mode():
    with pytest.raises(SystemExit) as exc:
        main(["--nvd-cve", "CVE-2025-12345", "--modified-since", "2026-10-01T00:00:00Z"])
    assert exc.value.code == 2


def test_modified_until_without_since_is_rejected_by_cli(monkeypatch):
    monkeypatch.setattr("sentinela.cli.search_cves", lambda *_args, **_kwargs: [])
    with pytest.raises(SystemExit) as exc:
        main(["--nvd-search", "OpenSSH", "--modified-until", "2026-10-02T00:00:00Z"])
    assert exc.value.code == 2
