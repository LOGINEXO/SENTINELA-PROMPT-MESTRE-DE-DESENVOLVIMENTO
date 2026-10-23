import json

import pytest

from sentinela.audit.__main__ import main


def test_standalone_audit_cli_emits_common_report(monkeypatch, capsys):
    monkeypatch.setattr("sentinela.audit.__main__.load_scope", lambda _path: {"example.com"})
    monkeypatch.setattr("sentinela.audit.__main__.audit_https", lambda host, **_kwargs: {
        "target": host, "http_status": 200, "tls": {"verified": True}
    })
    assert main(["example.com"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["source"] == "passive-https-audit"
    assert report["results"][0]["target"] == "example.com"


def test_standalone_audit_cli_exports_report(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sentinela.audit.__main__.load_scope", lambda _path: {"example.com"})
    monkeypatch.setattr("sentinela.audit.__main__.audit_https", lambda host, **_kwargs: {"target": host})
    assert main(["example.com", "--export-json", "passive.json"]) == 0
    stored = json.loads((tmp_path / "reports" / "passive.json").read_text(encoding="utf-8"))
    assert stored["results"][0]["target"] == "example.com"
    assert "Relatório JSON salvo" in capsys.readouterr().err


def test_standalone_audit_cli_reports_invalid_target(monkeypatch):
    from sentinela.audit.passive import PassiveAuditError

    monkeypatch.setattr("sentinela.audit.__main__.load_scope", lambda _path: {"example.com"})

    def fail(_host, **_kwargs):
        raise PassiveAuditError("hostname inválido")

    monkeypatch.setattr("sentinela.audit.__main__.audit_https", fail)
    with pytest.raises(SystemExit) as exc:
        main(["localhost"])
    assert exc.value.code == 2


def test_standalone_audit_cli_fails_closed_without_scope(monkeypatch):
    from sentinela.scope import ScopeError

    def fail(_path):
        raise ScopeError("arquivo de escopo ausente")

    monkeypatch.setattr("sentinela.audit.__main__.load_scope", fail)
    monkeypatch.setattr("sentinela.audit.__main__.audit_https",
                        lambda *_args, **_kwargs: pytest.fail("auditoria não deveria executar"))
    with pytest.raises(SystemExit) as exc:
        main(["example.com"])
    assert exc.value.code == 2
