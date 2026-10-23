import json
import re

import pytest

from sentinela import queue
from sentinela.email_drafts import EmailDraftError, create_email_draft, render_email_draft


def _completed_nvd_job(tmp_path, monkeypatch):
    monkeypatch.setenv("SENTINELA_QUEUE_DB", str(tmp_path / "queue.sqlite3"))
    job = queue.enqueue("nvd_search", {"query": "OpenSSH", "limit": 5})
    queue.claim_next()
    queue.finish(job["id"], result={
        "source": "NVD",
        "record_count": 1,
        "results": [{
            "cve_id": "CVE-2024-12345",
            "technical_priority": "high",
            "cvss": {"base_score": 8.1},
            "description": "Sample public vulnerability.",
            "nvd_url": "https://nvd.nist.gov/vuln/detail/CVE-2024-12345",
            "asset_confirmed": False,
            "api_key": "should-not-leak",
        }],
    })
    return job["id"]


def test_create_draft_from_completed_job_without_sending(tmp_path, monkeypatch):
    job_id = _completed_nvd_job(tmp_path, monkeypatch)
    output = create_email_draft(job_id, output_dir=tmp_path / "drafts")
    content = output.read_text(encoding="utf-8")
    assert output.name == f"job-{job_id}.md"
    assert "RASCUNHO NÃO ENVIADO" in content
    assert "CVE-2024-12345" in content
    assert "não confirmam exposição" in content
    assert "should-not-leak" not in content
    assert "Para:** [preencher e revisar destinatários]" in content


def test_draft_requires_completed_supported_job(tmp_path, monkeypatch):
    monkeypatch.setenv("SENTINELA_QUEUE_DB", str(tmp_path / "queue.sqlite3"))
    job = queue.enqueue("nvd_search", {"query": "OpenSSH"})
    with pytest.raises(EmailDraftError):
        render_email_draft(queue.get_job(job["id"]))


def test_missing_job_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("SENTINELA_QUEUE_DB", str(tmp_path / "queue.sqlite3"))
    with pytest.raises(EmailDraftError):
        create_email_draft(999, output_dir=tmp_path / "drafts")


def test_invalid_job_id_rejected():
    with pytest.raises(EmailDraftError):
        create_email_draft(0)


def test_draft_file_overwrites_atomically(tmp_path, monkeypatch):
    job_id = _completed_nvd_job(tmp_path, monkeypatch)
    output = create_email_draft(job_id, output_dir=tmp_path / "drafts")
    first = output.read_text(encoding="utf-8")
    second = create_email_draft(job_id, output_dir=tmp_path / "drafts")
    second_content = second.read_text(encoding="utf-8")

    assert second == output
    # The generated-at timestamp legitimately changes between writes.
    timestamp = r"(?m)^\*\*Gerado em \(UTC\):\*\* .*?$"
    assert re.sub(timestamp, "", first) == re.sub(timestamp, "", second_content)
    assert re.search(timestamp, second_content)
