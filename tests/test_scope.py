import socket

import pytest

from sentinela import scope
from sentinela.scope import ScopeError, canonical_hostname, load_scope, require_in_scope, validate_redirect


def test_canonical_hostname_normalizes_only_https_origin():
    assert canonical_hostname("EXAMPLE.COM") == "example.com"
    assert canonical_hostname("https://example.com/") == "example.com"


@pytest.mark.parametrize("value", [
    "", "http://example.com", "https://example.com:444",
    "https://user@example.com", "https://example.com/path",
    "127.0.0.1", "localhost", "*.example.com", "example.com?q=x",
])
def test_canonical_hostname_rejects_ambiguous_inputs(value):
    with pytest.raises(ScopeError):
        canonical_hostname(value)


def test_scope_file_ignores_comments_and_requires_exact_hosts(tmp_path):
    path = tmp_path / "scope.txt"
    path.write_text("# authorized domains\nEXAMPLE.com\n\nexample.org # another\n", encoding="utf-8")
    assert load_scope(path) == frozenset({"example.com", "example.org"})
    assert require_in_scope("https://example.com/", load_scope(path)) == "example.com"
    with pytest.raises(ScopeError, match="fora do escopo"):
        require_in_scope("sub.example.com", load_scope(path))


def test_scope_file_fails_closed_when_missing_or_empty(tmp_path):
    with pytest.raises(ScopeError, match="Não foi possível ler"):
        load_scope(tmp_path / "missing.txt")
    empty = tmp_path / "empty.txt"
    empty.write_text("# no targets yet\n", encoding="utf-8")
    with pytest.raises(ScopeError, match="não contém"):
        load_scope(empty)


def test_scope_file_rejects_wildcards(tmp_path):
    path = tmp_path / "scope.txt"
    path.write_text("*.example.com\n", encoding="utf-8")
    with pytest.raises(ScopeError, match="Curingas"):
        load_scope(path)


def test_dns_resolution_rejects_private_and_mixed_answers(monkeypatch):
    monkeypatch.setattr(scope.socket, "getaddrinfo", lambda *_args, **_kwargs: [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443)),
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.10", 443)),
    ])
    with pytest.raises(ScopeError, match="não público"):
        scope.resolve_public_addresses("example.com")


def test_redirect_validation_allows_only_scoped_public_https(monkeypatch):
    monkeypatch.setattr(scope, "resolve_public_addresses", lambda _host: ["8.8.8.8"])
    result = validate_redirect("https://example.com/start", "/next?q=1#fragment",
                               allowed_hosts={"example.com"})
    assert result == {
        "url": "https://example.com/next?q=1",
        "hostname": "example.com",
        "resolved_public_ips": ["8.8.8.8"],
    }


@pytest.mark.parametrize("location", [
    "http://example.com/", "https://outside.example/", "//outside.example/path",
    "https://user@example.com/", "https://example.com:444/",
])
def test_redirect_validation_rejects_unsafe_or_out_of_scope_destination(monkeypatch, location):
    monkeypatch.setattr(scope, "resolve_public_addresses", lambda _host: ["8.8.8.8"])
    with pytest.raises(ScopeError):
        validate_redirect("https://example.com/start", location, allowed_hosts={"example.com"})
