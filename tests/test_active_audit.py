import socket
import ssl

import pytest

from sentinela.audit import active
from sentinela.audit.active import ActiveAuditError, audit_https_get


def test_active_check_requires_exact_allowlist_before_dns(monkeypatch):
    monkeypatch.setattr(active, "_resolve_public_addresses",
                        lambda _host: pytest.fail("DNS não deveria ser consultado"))
    with pytest.raises(ActiveAuditError, match="fora do escopo"):
        audit_https_get("other.example", allowed_hosts={"example.com"})


def test_active_check_rejects_invalid_timeout_before_dns(monkeypatch):
    monkeypatch.setattr(active, "_resolve_public_addresses",
                        lambda _host: pytest.fail("DNS não deveria ser consultado"))
    with pytest.raises(ActiveAuditError, match="timeout"):
        audit_https_get("example.com", allowed_hosts={"example.com"}, timeout=20)


def test_active_check_pins_public_ip_and_discards_bounded_response(monkeypatch):
    monkeypatch.setattr(active, "_resolve_public_addresses", lambda _host: ["8.8.8.8"])
    events = []

    class FakeTLS:
        def settimeout(self, timeout): events.append(("timeout", timeout))
        def sendall(self, request): events.append(("request", request.decode("ascii")))
        def version(self): return "TLSv1.3"
        def cipher(self): return ("TLS_AES_128_GCM_SHA256", "TLSv1.3", 128)
        def close(self): events.append(("close",))
    
    fake_tls = FakeTLS()
    class FakeRaw:
        def close(self): events.append(("raw-close",))
    monkeypatch.setattr(active.socket, "create_connection", lambda address, timeout: (events.append(("connect", address, timeout)) or FakeRaw()))
    monkeypatch.setattr(active.ssl, "create_default_context", lambda: type("Context", (), {"wrap_socket": lambda self, raw, server_hostname: (events.append(("sni", server_hostname)) or fake_tls)})())

    class FakeResponse:
        status = 200
        def __init__(self, sock): pass
        def begin(self): pass
        def getheaders(self): return [("Content-Type", "text/html"), ("Set-Cookie", "secret=not-reported")]
        def read(self, size):
            events.append(("read", size))
            return b"x" * size

    monkeypatch.setattr(active.http.client, "HTTPResponse", FakeResponse)
    result = audit_https_get("example.com", allowed_hosts={"example.com"})
    assert ("connect", ("8.8.8.8", 443), 5.0) in events
    assert ("sni", "example.com") in events
    request = next(item[1] for item in events if item[0] == "request")
    assert request.startswith("GET / HTTP/1.1\r\n")
    assert "POST " not in request
    assert ("read", active.MAX_BODY_BYTES + 1) in events
    assert result["request_count"] == 1
    assert result["http_status"] == 200
    assert result["response_body"] == "discarded"
    assert result["response_sample_truncated"] is True
    assert "set-cookie" not in result["response_headers"]
    assert result["redirect_followed"] is False


def test_active_check_rejects_tls_verification_failure(monkeypatch):
    monkeypatch.setattr(active, "_resolve_public_addresses", lambda _host: ["8.8.8.8"])
    class FakeRaw:
        def close(self): pass
    monkeypatch.setattr(active.socket, "create_connection", lambda *_a, **_k: FakeRaw())
    class Context:
        def wrap_socket(self, *_a, **_k):
            raise ssl.SSLCertVerificationError("private details")
    monkeypatch.setattr(active.ssl, "create_default_context", lambda: Context())
    with pytest.raises(ActiveAuditError, match="validação do certificado TLS falhou"):
        audit_https_get("example.com", allowed_hosts={"example.com"})
