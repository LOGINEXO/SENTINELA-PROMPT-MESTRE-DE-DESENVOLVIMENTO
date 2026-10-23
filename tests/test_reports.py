import json
from pathlib import Path

import pytest

from sentinela.reports import ReportError, build_report, export_json_report, sanitize


def test_build_report_has_stable_envelope_and_timestamp():
    report = build_report([{"cve_id": "CVE-2025-12345"}], source="NVD")
    assert report["schema_version"] == "1.0"
    assert report["source"] == "NVD"
    assert report["record_count"] == 1
    assert report["results"][0]["cve_id"] == "CVE-2025-12345"
    assert report["generated_at"].endswith("Z")


def test_sanitize_redacts_sensitive_keys_recursively():
    result = sanitize({
        "api_key": "secret-value",
        "nested": [{"password": "p@ss", "description": "public"}],
    })
    assert result == {
        "api_key": "[REDACTED]",
        "nested": [{"password": "[REDACTED]", "description": "public"}],
    }


def test_sanitize_redacts_common_secret_strings():
    result = sanitize({
        "message": "Bearer abc.def and token=xyz",
        "url": "https://example.test/?api_key=secret&ok=1",
    })
    assert "abc.def" not in result["message"]
    assert "xyz" not in result["message"]
    assert "secret" not in result["url"]
    assert "ok=1" in result["url"]


def test_export_writes_valid_sanitized_json_atomically(tmp_path):
    reports = tmp_path / "reports"
    output = export_json_report(
        [{"cve_id": "CVE-2025-12345", "authorization": "Bearer secret"}],
        "run-001.json", source="NVD", reports_dir=reports,
    )
    parsed = json.loads(output.read_text(encoding="utf-8"))
    assert output == reports / "run-001.json"
    assert parsed["record_count"] == 1
    assert parsed["results"][0]["authorization"] == "[REDACTED]"
    assert list(reports.glob("*.tmp")) == []


def test_export_rejects_path_traversal(tmp_path):
    with pytest.raises(ReportError, match="dentro do diretório reports"):
        export_json_report([], "../outside.json", source="NVD", reports_dir=tmp_path / "reports")


def test_export_rejects_non_json_extension(tmp_path):
    with pytest.raises(ReportError, match="extensão .json"):
        export_json_report([], "report.txt", source="NVD", reports_dir=tmp_path / "reports")


def test_report_rejects_non_object_records():
    with pytest.raises(ReportError, match="lista de objetos"):
        build_report([{"ok": True}, "bad"], source="NVD")


def test_report_rejects_non_finite_json_values(tmp_path):
    with pytest.raises(ReportError, match="gravar o relatório JSON"):
        export_json_report([{"score": float("nan")}], "invalid.json",
                           source="NVD", reports_dir=tmp_path / "reports")
