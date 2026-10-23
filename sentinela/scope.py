"""Explicit hostname allowlist for authorized passive checks."""
from __future__ import annotations
import ipaddress
import re
import socket
from pathlib import Path
from urllib.parse import urlsplit, urljoin, urlunsplit

_LABEL = re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$")

class ScopeError(ValueError):
    """Raised when a hostname is invalid or outside explicit authorization."""

def canonical_hostname(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ScopeError("Informe um hostname válido.")
    raw = value.strip()
    parsed = urlsplit(raw if "://" in raw else "https://" + raw)
    try:
        port = parsed.port
    except ValueError as exc:
        raise ScopeError("Porta inválida.") from exc
    if parsed.scheme.lower() != "https" or parsed.username is not None or parsed.password is not None:
        raise ScopeError("Somente HTTPS sem credenciais é permitido.")
    if port not in (None, 443) or parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise ScopeError("Informe apenas o hostname HTTPS na porta 443.")
    host = (parsed.hostname or "").rstrip(".").lower()
    if not host or len(host) > 253 or "." not in host:
        raise ScopeError("Informe um hostname DNS completo.")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ScopeError("Endereços IP literais não são aceitos.")
    if any(not _LABEL.fullmatch(label) for label in host.split(".")):
        raise ScopeError("Hostname DNS inválido.")
    if host.endswith((".localhost", ".local", ".internal", ".test", ".invalid")):
        raise ScopeError("Hostname local ou reservado não permitido.")
    return host

def load_scope(path: str | Path) -> frozenset[str]:
    file = Path(path)
    try:
        lines = file.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ScopeError(f"Não foi possível ler o arquivo de escopo: {file}.") from exc
    hosts = set()
    for number, line in enumerate(lines, 1):
        entry = line.split("#", 1)[0].strip()
        if not entry:
            continue
        if "*" in entry:
            raise ScopeError(f"Curingas não permitidos (linha {number}).")
        try:
            hosts.add(canonical_hostname(entry))
        except ScopeError as exc:
            raise ScopeError(f"Entrada inválida na linha {number}: {exc}") from exc
    if not hosts:
        raise ScopeError(f"O arquivo {file} não contém hostnames autorizados.")
    return frozenset(hosts)

def require_in_scope(target: str, allowed_hosts: set[str] | frozenset[str]) -> str:
    host = canonical_hostname(target)
    scope = {canonical_hostname(item) for item in allowed_hosts}
    if host not in scope:
        raise ScopeError(f"Destino fora do escopo autorizado: {host}.")
    return host

def resolve_public_addresses(hostname: str) -> list[str]:
    try:
        answers = socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise ScopeError("Não foi possível resolver o hostname autorizado.") from exc
    result = []
    for answer in answers:
        try:
            address = ipaddress.ip_address(answer[4][0])
        except (ValueError, IndexError, TypeError) as exc:
            raise ScopeError("A resolução DNS retornou endereço inválido.") from exc
        if not address.is_global:
            raise ScopeError("Destino bloqueado: DNS contém endereço IP não público.")
        if str(address) not in result:
            result.append(str(address))
    if not result:
        raise ScopeError("O hostname não possui endereços públicos utilizáveis.")
    return result

def validate_redirect(source_url: str, location: str, *, allowed_hosts: set[str] | frozenset[str]) -> dict[str, object]:
    """Validate a Location destination without sending a request to it."""
    if not isinstance(location, str) or not location.strip():
        raise ScopeError("Cabeçalho Location vazio ou inválido.")
    source = urlsplit(source_url)
    if source.scheme.lower() != "https" or not source.hostname:
        raise ScopeError("Origem do redirecionamento inválida.")
    candidate = urlsplit(urljoin(source_url, location.strip()))
    if candidate.scheme.lower() != "https":
        raise ScopeError("Redirecionamento para HTTP ou esquema não HTTPS bloqueado.")
    try:
        port = candidate.port
    except ValueError as exc:
        raise ScopeError("Porta inválida no redirecionamento.") from exc
    if port not in (None, 443) or candidate.username is not None or candidate.password is not None:
        raise ScopeError("Porta ou credenciais não permitidas no redirecionamento.")
    host = require_in_scope(candidate.hostname or "", allowed_hosts)
    ips = resolve_public_addresses(host)
    return {"url": urlunsplit(("https", host, candidate.path or "/", candidate.query, "")), "hostname": host, "resolved_public_ips": ips}
