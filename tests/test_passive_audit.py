import socket
import ssl

import pytest

from sentinela.audit import passive
from sentinela.audit.passive import PassiveAuditError, _validate_hostname, audit_https


def test_validate_hostname_accepts_https_host_only():
    assert _validate_hostname("https://example.com/") == "example.com"
    assert _validate_hostname("EXAMPLE.COM") == "example.com"


@pytest.mark.parametrize("target", [
    "", "http://example.com", "https://example.com:8443",
    "https://user:pass@example.com", "https://example.com/path",
    "localhost", "service.local", "192.0.2.10", "example.com?token=x",
])
def test_validate_hostname_rejects_unsafe_or_unsupported_targets(target):
    with pytest.raises(PassiveAuditError):
        _validate_hostname(target)


def test_dns_resolution_rejects_private_address(monkeypatch):
    monkeypatch.setattr(passive.socket, "getaddrinfo", lambda *_args, **_kwargs: [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))
    ])
    with pytest.raises(PassiveAuditError, match="não público"):
        passive._resolve_public_addresses("example.com")


def test_dns_resolution_rejects_mixed_public_and_private_answers(monkeypatch):
    monkeypatch.setattr(passive.socket, "getaddrinfo", lambda *_args, **_kwargs: [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443)),
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.2", 443)),
    ])
    with pytest.raises(PassiveAuditError, match="não público"):
        passive._resolve_public_addresses("example.com")


def test_dns_resolution_returns_unique_public_addresses(monkeypatch):
    monkeypatch.setattr(passive.socket, "getaddrinfo", lambda *_args, **_kwargs: [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443)),
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443)),
    ])
    assert passive._resolve_public_addresses("example.com") == ["8.8.8.8"]


def test_audit_reports_tls_and_security_headers_without_following_redirects(monkeypatch):
    monkeypatch.setattr(passive, "_resolve_public_addresses", lambda _host: ["8.8.8.8"])

    class FakeSocket:
        def getpeercert(self):
            return {"subject": ((("commonName", "example.com"),),),
                    "issuer": ((("commonName", "Example CA"),),),
                    "notAfter": "Dec 31 23:59:59 2030 GMT"}
        def version(self):
            return "TLSv1.3"
        def cipher(self):
            return ("TLS_AES_128_GCM_SHA256", "TLSv1.3", 128)

    class FakeResponse:
        status = 302
        def getheaders(self):
            return [("Location", "https://other.example/"), ("Strict-Transport-Security", "max-age=31536000")]

    class FakeConnection:
        def __init__(self, hostname, ip, timeout):
            assert hostname == "example.com"
            assert ip == "8.8.8.8"
            assert timeout == 5
            self.sock = FakeSocket()
            self.response = FakeResponse()
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(passive, "_PinnedHTTPSConnection", FakeConnection)
    result = audit_https("https://example.com", allowed_hosts={"example.com"})
    assert result["http_status"] == 302
    assert result["redirect_followed"] is False
    assert result["tls"]["verified"] is True
    assert result["tls"]["version"] == "TLSv1.3"
    assert result["security_headers"]["strict-transport-security"]["present"] is True
    assert result["security_headers"]["content-security-policy"]["present"] is False


def test_audit_rejects_invalid_timeout_before_network(monkeypatch):
    monkeypatch.setattr(passive, "_resolve_public_addresses",
                        lambda _host: pytest.fail("DNS não deveria ser consultado"))
    with pytest.raises(PassiveAuditError, match="timeout"):
        audit_https("example.com", allowed_hosts={"example.com"}, timeout=100)


def test_audit_rejects_target_outside_allowlist_before_dns(monkeypatch):
    monkeypatch.setattr(passive, "_resolve_public_addresses",
                        lambda _host: pytest.fail("DNS não deveria ser consultado"))
    with pytest.raises(PassiveAuditError, match="fora do escopo"):
        audit_https("other.example", allowed_hosts={"example.com"})


def test_tls_verification_error_is_reported_safely(monkeypatch):
    monkeypatch.setattr(passive, "_resolve_public_addresses", lambda _host: ["8.8.8.8"])

    class FailedConnection:
        def __init__(self, *_args, **_kwargs): pass
        def __enter__(self): raise ssl.SSLCertVerificationError("details")
        def __exit__(self, *_args): return False

    monkeypatch.setattr(passive, "_PinnedHTTPSConnection", FailedConnection)
    with pytest.raises(PassiveAuditError, match="certificado TLS falhou"):
        audit_https("example.com", allowed_hosts={"example.com"})
