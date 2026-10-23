import json

import pytest

from sentinela.audit.__main__ import main


def test_standalone_audit_cli_emits_common_report(monkeypatch, capsys):
    monkeypatch.setattr("sentinela.audit.__main__.audit_https", lambda host: {
        "target": host, "http_status": 200, "tls": {"verified": True}
    })
    assert main(["example.com"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["source"] == "passive-https-audit"
    assert report["results"][0]["target"] == "example.com"


def test_standalone_audit_cli_exports_report(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sentinela.audit.__main__.audit_https", lambda host: {"target": host})
    assert main(["example.com", "--export-json", "passive.json"]) == 0
    stored = json.loads((tmp_path / "reports" / "passive.json").read_text(encoding="utf-8"))
    assert stored["results"][0]["target"] == "example.com"
    assert "Relatório JSON salvo" in capsys.readouterr().err


def test_standalone_audit_cli_reports_invalid_target(monkeypatch):
    from sentinela.audit.passive import PassiveAuditError

    def fail(_host):
        raise PassiveAuditError("hostname inválido")

    monkeypatch.setattr("sentinela.audit.__main__.audit_https", fail)
    with pytest.raises(SystemExit) as exc:
        main(["localhost"])
    assert exc.value.code == 2
