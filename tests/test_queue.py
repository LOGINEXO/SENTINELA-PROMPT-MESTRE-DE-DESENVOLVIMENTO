import json

import pytest

from sentinela import queue


def test_enqueue_and_claim_job(tmp_path, monkeypatch):
    monkeypatch.setenv("SENTINELA_QUEUE_DB", str(tmp_path / "queue.sqlite3"))
    job = queue.enqueue("nvd_search", {"query": "OpenSSH", "limit": 5})
    assert job["status"] == "queued"
    assert job["payload"] == {"query": "OpenSSH", "limit": 5}
    claimed = queue.claim_next()
    assert claimed["id"] == job["id"]
    assert claimed["status"] == "running"
    queue.finish(job["id"], result={"ok": True})
    current = queue.status()
    assert current["counts"]["completed"] == 1
    assert current["jobs"][0]["result"] == {"ok": True}


def test_pause_blocks_claim_until_play(tmp_path, monkeypatch):
    monkeypatch.setenv("SENTINELA_QUEUE_DB", str(tmp_path / "queue.sqlite3"))
    queue.enqueue("nvd_search", {"query": "OpenSSH"})
    queue.set_mode("pause")
    assert queue.claim_next() is None
    queue.set_mode("play")
    assert queue.claim_next()["status"] == "running"


def test_stop_cancels_queued_jobs_and_requires_play(tmp_path, monkeypatch):
    monkeypatch.setenv("SENTINELA_QUEUE_DB", str(tmp_path / "queue.sqlite3"))
    job = queue.enqueue("nvd_search", {"query": "OpenSSH"})
    result = queue.set_mode("stop")
    assert result["mode"] == "stopped"
    assert result["counts"]["stopped"] == 1
    assert queue.claim_next() is None
    queue.set_mode("play")
    assert queue.claim_next() is None
    assert queue.status()["jobs"][0]["status"] == "stopped"


def test_stop_during_running_task_marks_it_stopped_on_finish(tmp_path, monkeypatch):
    monkeypatch.setenv("SENTINELA_QUEUE_DB", str(tmp_path / "queue.sqlite3"))
    job = queue.enqueue("nvd_search", {"query": "OpenSSH"})
    queue.claim_next()
    queue.set_mode("stop")
    queue.finish(job["id"], result={"ok": True})
    assert queue.status()["jobs"][0]["status"] == "stopped"


def test_invalid_tasks_and_payloads_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("SENTINELA_QUEUE_DB", str(tmp_path / "queue.sqlite3"))
    with pytest.raises(queue.QueueError):
        queue.enqueue("shell", {"command": "whoami"})
    with pytest.raises(queue.QueueError):
        queue.enqueue("nvd_search", {"query": " "})
    with pytest.raises(queue.QueueError):
        queue.enqueue("nvd_search", {"query": "OpenSSH", "limit": 1000})


def test_audit_requires_scope_allowlist(tmp_path, monkeypatch):
    monkeypatch.setenv("SENTINELA_QUEUE_DB", str(tmp_path / "queue.sqlite3"))
    scope = tmp_path / "scope.txt"
    scope.write_text("example.com\n", encoding="utf-8")
    monkeypatch.setenv("SENTINELA_SCOPE_FILE", str(scope))
    job = queue.enqueue("passive_audit", {"host": "example.com"})
    assert job["payload"]["host"] == "example.com"
    with pytest.raises(Exception):
        queue.enqueue("passive_audit", {"host": "other.example"})


def test_active_audit_requires_separate_allowlist_and_confirmation(tmp_path, monkeypatch):
    monkeypatch.setenv("SENTINELA_QUEUE_DB", str(tmp_path / "queue.sqlite3"))
    active_scope = tmp_path / "active-scope.txt"
    active_scope.write_text("active.example.com\n", encoding="utf-8")
    monkeypatch.setenv("SENTINELA_ACTIVE_SCOPE_FILE", str(active_scope))
    with pytest.raises(queue.QueueError, match="confirm-authorized"):
        queue.enqueue("active_audit", {"host": "active.example.com"})
    job = queue.enqueue("active_audit", {"host": "active.example.com", "confirm_authorized": True})
    assert job["task_type"] == "active_audit"
    assert job["payload"] == {"host": "active.example.com", "confirm_authorized": True}
    with pytest.raises(queue.QueueError, match="fora do escopo"):
        queue.enqueue("active_audit", {"host": "other.example.com", "confirm_authorized": True})
