"""Single-request, bounded active HTTPS check for explicitly authorized hosts."""
from __future__ import annotations

from datetime import datetime, timezone
import http.client
import ipaddress
import socket
import ssl
from typing import Any

from sentinela.audit.passive import _validate_hostname, _resolve_public_addresses, DEFAULT_TIMEOUT_SECONDS, MAX_TIMEOUT_SECONDS
from sentinela.scope import ScopeError, require_in_scope


class ActiveAuditError(ValueError):
    """Raised when an active check is invalid or outside its authorization scope."""


MAX_BODY_BYTES = 8192


def audit_https_get(
    target: str,
    *,
    allowed_hosts: set[str] | frozenset[str],
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Perform exactly one GET / to a separately authorized host; never follow redirects."""
    try:
        hostname = require_in_scope(target, allowed_hosts)
    except ScopeError as exc:
        raise ActiveAuditError(str(exc)) from exc
    hostname = _validate_hostname(target)
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout <= MAX_TIMEOUT_SECONDS:
        raise ActiveAuditError(f"timeout deve ser maior que zero e no máximo {MAX_TIMEOUT_SECONDS:g} segundos.")
    addresses = _resolve_public_addresses(hostname)
    raw: socket.socket | None = None
    tls: ssl.SSLSocket | None = None
    try:
        raw = socket.create_connection((addresses[0], 443), timeout=float(timeout))
        context = ssl.create_default_context()
        tls = context.wrap_socket(raw, server_hostname=hostname)
        tls.settimeout(float(timeout))
        request = (
            f"GET / HTTP/1.1\r\nHost: {hostname}\r\n"
            "User-Agent: Sentinela/0.3.0 (authorized-active-check)\r\n"
            "Accept: text/html,application/json;q=0.9,*/*;q=0.1\r\n"
            "Connection: close\r\n\r\n"
        )
        tls.sendall(request.encode("ascii"))
        response = http.client.HTTPResponse(tls)
        response.begin()
        status = response.status
        headers = {key.lower(): value.strip()[:500] for key, value in response.getheaders() if key.lower() in {
            "content-type", "content-length", "cache-control", "server", "location", "allow"
        }}
        # Read only a tiny capped sample to prove a GET response, then discard it.
        sample = response.read(MAX_BODY_BYTES + 1)
        truncated = len(sample) > MAX_BODY_BYTES
        sample = sample[:MAX_BODY_BYTES]
        tls_version = tls.version()
        cipher = tls.cipher()
        body_bytes_read = len(sample)
    except ssl.SSLCertVerificationError as exc:
        raise ActiveAuditError("A validação do certificado TLS falhou; resultado não confiável.") from exc
    except (ssl.SSLError, socket.timeout, TimeoutError, OSError, http.client.HTTPException) as exc:
        raise ActiveAuditError(f"Falha na verificação HTTPS ativa: {type(exc).__name__}.") from exc
    finally:
        if tls is not None:
            tls.close()
        elif raw is not None:
            raw.close()
    return {
        "target": hostname,
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "mode": "authorized-active",
        "method": "GET",
        "path": "/",
        "port": 443,
        "request_count": 1,
        "resolved_public_ips": addresses,
        "http_status": status,
        "redirect_followed": False,
        "response_body": "discarded",
        "response_body_bytes_sampled": body_bytes_read,
        "response_sample_truncated": truncated,
        "response_headers": headers,
        "tls": {"verified": True, "version": tls_version, "cipher": cipher[0] if cipher else None},
        "notes": [
            "Um único GET para a raiz foi executado mediante escopo de autorização ativa separado.",
            "O corpo da resposta foi descartado; no máximo 8192 bytes são lidos para limitar consumo.",
            "Redirecionamentos não são seguidos; nenhuma exploração, enumeração de diretórios ou varredura de portas é realizada.",
            "Este teste limitado não constitui teste de penetração nem certificação de segurança.",
        ],
    }
