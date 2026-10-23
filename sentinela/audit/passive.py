"""Bounded passive HTTPS/TLS/header audit for explicitly authorized hostnames.

This module sends one HTTPS HEAD request to the selected hostname on port 443.
It verifies the TLS certificate, validates every DNS answer as a public IP, pins
the TCP connection to a validated address, and never follows redirects.
"""
from __future__ import annotations

from datetime import datetime, timezone
import http.client
import ipaddress
import json
import re
import socket
import ssl
from typing import Any
from urllib.parse import urlsplit

DEFAULT_TIMEOUT_SECONDS = 5.0
MAX_TIMEOUT_SECONDS = 15.0
_HOST_LABEL = re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$")
SECURITY_HEADERS = (
    "strict-transport-security",
    "content-security-policy",
    "x-content-type-options",
    "x-frame-options",
    "referrer-policy",
    "permissions-policy",
)


class PassiveAuditError(ValueError):
    """Raised when the target or passive audit response is unsafe or invalid."""


class _PinnedHTTPSConnection:
    """Small HTTP/1.1 HEAD client connected to a prevalidated IP address."""

    def __init__(self, hostname: str, ip: str, timeout: float):
        self.hostname = hostname
        self.ip = ip
        self.timeout = timeout
        self.sock: ssl.SSLSocket | None = None

    def __enter__(self):
        raw = socket.create_connection((self.ip, 443), timeout=self.timeout)
        try:
            context = ssl.create_default_context()
            self.sock = context.wrap_socket(raw, server_hostname=self.hostname)
            self.sock.settimeout(self.timeout)
            request = (
                f"HEAD / HTTP/1.1\r\nHost: {self.hostname}\r\n"
                "User-Agent: Sentinela/0.3.0 (passive-security-audit)\r\n"
                "Accept: */*\r\nConnection: close\r\n\r\n"
            )
            self.sock.sendall(request.encode("ascii"))
            self.response = http.client.HTTPResponse(self.sock)
            self.response.begin()
            return self
        except Exception:
            raw.close()
            raise

    def __exit__(self, *_args):
        if self.sock is not None:
            self.sock.close()
        return False


def _validate_hostname(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PassiveAuditError("Informe um hostname ou URL HTTPS válido.")
    raw = value.strip()
    parsed = urlsplit(raw if "://" in raw else "https://" + raw)
    if parsed.scheme.lower() != "https":
        raise PassiveAuditError("A auditoria passiva aceita somente HTTPS.")
    if parsed.username or parsed.password:
        raise PassiveAuditError("URLs com credenciais embutidas não são aceitas.")
    if parsed.port not in (None, 443):
        raise PassiveAuditError("Somente a porta HTTPS padrão 443 é permitida.")
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise PassiveAuditError("Informe somente o hostname; caminhos, consultas e fragmentos não são aceitos.")
    hostname = (parsed.hostname or "").rstrip(".").lower()
    if not hostname or len(hostname) > 253 or "." not in hostname:
        raise PassiveAuditError("Informe um hostname DNS completo, não um nome local.")
    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        raise PassiveAuditError("Informe um hostname DNS, não um endereço IP literal.")
    if any(not _HOST_LABEL.fullmatch(label) for label in hostname.split(".")):
        raise PassiveAuditError("Hostname contém rótulos DNS inválidos.")
    if hostname == "localhost" or hostname.endswith((".localhost", ".local", ".internal", ".test", ".invalid")):
        raise PassiveAuditError("Hostnames locais ou reservados não podem ser auditados.")
    return hostname


def _resolve_public_addresses(hostname: str) -> list[str]:
    try:
        answers = socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
    except (OSError, socket.gaierror) as exc:
        raise PassiveAuditError("Não foi possível resolver o hostname informado.") from exc
    addresses: list[str] = []
    for answer in answers:
        try:
            address = ipaddress.ip_address(answer[4][0])
        except ValueError as exc:
            raise PassiveAuditError("A resolução DNS retornou um endereço inválido.") from exc
        if not address.is_global:
            raise PassiveAuditError("O hostname resolve para IP não público; a consulta foi bloqueada.")
        if str(address) not in addresses:
            addresses.append(str(address))
    if not addresses:
        raise PassiveAuditError("O hostname não possui endereços públicos utilizáveis.")
    return addresses


def audit_https(
    target: str,
    *,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Perform one passive HEAD request and report TLS/header observations."""
    hostname = _validate_hostname(target)
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout <= MAX_TIMEOUT_SECONDS:
        raise PassiveAuditError(f"timeout deve ser maior que zero e no máximo {MAX_TIMEOUT_SECONDS:g} segundos.")
    addresses = _resolve_public_addresses(hostname)
    # Pin to the first validated public IP. No automatic redirects or retries.
    try:
        with _PinnedHTTPSConnection(hostname, addresses[0], float(timeout)) as connection:
            response = connection.response
            response_headers = {name.lower(): value.strip() for name, value in response.getheaders()}
            certificate = connection.sock.getpeercert() if connection.sock else {}
            tls_version = connection.sock.version() if connection.sock else None
            cipher = connection.sock.cipher() if connection.sock else None
            status = response.status
    except ssl.SSLCertVerificationError as exc:
        raise PassiveAuditError("A validação do certificado TLS falhou; resultado não confiável.") from exc
    except (ssl.SSLError, socket.timeout, TimeoutError, OSError, http.client.HTTPException) as exc:
        raise PassiveAuditError(f"Falha ao realizar a verificação HTTPS passiva: {type(exc).__name__}.") from exc

    header_results = {
        name: {
            "present": name in response_headers,
            "value": response_headers.get(name),
        }
        for name in SECURITY_HEADERS
    }
    return {
        "target": hostname,
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "method": "HEAD",
        "port": 443,
        "resolved_public_ips": addresses,
        "http_status": status,
        "redirect_followed": False,
        "tls": {
            "verified": True,
            "version": tls_version,
            "cipher": cipher[0] if cipher else None,
            "certificate_subject": certificate.get("subject", ()),
            "certificate_issuer": certificate.get("issuer", ()),
            "certificate_not_after": certificate.get("notAfter"),
        },
        "security_headers": header_results,
        "notes": [
            "Verificação passiva: uma requisição HEAD HTTPS, sem exploração.",
            "A ausência de um cabeçalho é um indicador para revisão, não prova isolada de vulnerabilidade.",
            "A disponibilidade de dados pode variar conforme CDN, proxy ou resposta do servidor.",
        ],
    }


def report_json(result: dict[str, Any]) -> str:
    """Serialize an audit observation as strict JSON."""
    return json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
