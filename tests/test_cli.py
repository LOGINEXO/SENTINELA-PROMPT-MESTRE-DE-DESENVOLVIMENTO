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


def test_nvd_search_prints_common_report_and_forwards_options(monkeypatch, capsys):
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
    report = json.loads(capsys.readouterr().out)
    assert report["source"] == "NVD"
    assert report["record_count"] == 1
    assert report["results"][0]["cve_id"] == "CVE-2025-12345"


def test_nvd_cve_prints_common_report(monkeypatch, capsys):
    monkeypatch.setattr("sentinela.cli.get_cve", lambda cve_id: {"cve_id": cve_id})
    assert main(["--nvd-cve", "CVE-2025-12345"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["record_count"] == 1
    assert report["results"] == [{"cve_id": "CVE-2025-12345"}]


def test_nvd_cve_not_found_prints_empty_report(monkeypatch, capsys):
    monkeypatch.setattr("sentinela.cli.get_cve", lambda _cve_id: None)
    assert main(["--nvd-cve", "CVE-2025-12345"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["results"] == []
    assert report["record_count"] == 0


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


def test_modified_until_without_since_is_rejected_by_cli():
    with pytest.raises(SystemExit) as exc:
        main(["--nvd-search", "OpenSSH", "--modified-until", "2026-10-02T00:00:00Z"])
    assert exc.value.code == 2


def test_export_json_requires_nvd_query():
    with pytest.raises(SystemExit) as exc:
        main(["--export-json", "run.json"])
    assert exc.value.code == 2


def test_export_json_cli_writes_report_under_reports_dir(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sentinela.cli.search_cves", lambda *_args, **_kwargs: [
        {"cve_id": "CVE-2025-12345", "api_key": "do-not-write"}
    ])
    assert main(["--nvd-search", "OpenSSH", "--export-json", "run.json"]) == 0
    stored = json.loads((tmp_path / "reports" / "run.json").read_text(encoding="utf-8"))
    assert stored["results"][0]["api_key"] == "[REDACTED]"
    stdout = capsys.readouterr().out
    assert "Relatório JSON salvo em reports/run.json" in stdout
    assert "do-not-write" not in stdout


def test_export_json_cli_rejects_path_traversal(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sentinela.cli.search_cves", lambda *_args, **_kwargs: [])
    with pytest.raises(SystemExit) as exc:
        main(["--nvd-search", "OpenSSH", "--export-json", "../outside.json"])
    assert exc.value.code == 2
