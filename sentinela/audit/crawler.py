"""Bounded same-host HTTPS crawler for explicitly authorized defensive review.

Only performs GET requests to the exact allowlisted hostname on port 443.
It does not submit forms, execute JavaScript, follow redirects, or test exploits.
"""
from __future__ import annotations

from datetime import datetime, timezone
from html.parser import HTMLParser
import http.client
import ipaddress
import socket
import ssl
from typing import Any
from urllib.parse import urljoin, urlsplit, urlunsplit

from sentinela.scope import ScopeError, require_in_scope
from sentinela.audit.passive import _resolve_public_addresses, _validate_hostname

DEFAULT_TIMEOUT_SECONDS = 5.0
MAX_TIMEOUT_SECONDS = 10.0
MAX_PAGES = 25
MAX_BODY_BYTES = 1_000_000
MAX_LINKS_PER_PAGE = 200
SECURITY_HEADERS = (
    "strict-transport-security",
    "content-security-policy",
    "x-content-type-options",
    "x-frame-options",
    "referrer-policy",
    "permissions-policy",
)
TECHNOLOGY_HEADERS = ("server", "x-powered-by", "x-generator")


class SiteCrawlError(ValueError):
    """Raised when an authorized crawl cannot be safely completed."""


class _Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.title_parts: list[str] = []
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "title":
            self._in_title = True
        if tag.lower() == "a":
            href = dict(attrs).get("href")
            if href and len(self.links) < MAX_LINKS_PER_PAGE:
                self.links.append(href)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title and len(self.title_parts) < 50:
            self.title_parts.append(data.strip())


def _request(hostname: str, path: str, timeout: float) -> dict[str, Any]:
    addresses = _resolve_public_addresses(hostname)
    last_error: Exception | None = None
    for ip in addresses[:2]:
        raw = None
        wrapped = None
        try:
            raw = socket.create_connection((ip, 443), timeout=timeout)
            context = ssl.create_default_context()
            wrapped = context.wrap_socket(raw, server_hostname=hostname)
            wrapped.settimeout(timeout)
            request_path = path if path.startswith("/") else "/"
            request = (
                f"GET {request_path} HTTP/1.1\r\nHost: {hostname}\r\n"
                "User-Agent: Sentinela/0.4.0 (authorized-site-review)\r\n"
                "Accept: text/html,application/xhtml+xml;q=0.9,*/*;q=0.1\r\n"
                "Accept-Encoding: identity\r\nConnection: close\r\n\r\n"
            )
            wrapped.sendall(request.encode("ascii", errors="strict"))
            response = http.client.HTTPResponse(wrapped)
            response.begin()
            headers = {k.lower(): v.strip() for k, v in response.getheaders()}
            if response.status in (301, 302, 303, 307, 308):
                response.read(0)
                return {"status": response.status, "headers": headers, "body": b"", "redirect": True}
            content_type = headers.get("content-type", "")
            if "text/html" not in content_type.lower() and "application/xhtml+xml" not in content_type.lower():
                response.read(0)
                return {"status": response.status, "headers": headers, "body": b"", "redirect": False}
            body = response.read(MAX_BODY_BYTES + 1)
            if len(body) > MAX_BODY_BYTES:
                body = body[:MAX_BODY_BYTES]
                truncated = True
            else:
                truncated = False
            return {"status": response.status, "headers": headers, "body": body,
                    "redirect": False, "truncated": truncated}
        except (OSError, ssl.SSLError, socket.timeout, TimeoutError, http.client.HTTPException) as exc:
            last_error = exc
        finally:
            if wrapped is not None:
                wrapped.close()
            elif raw is not None:
                raw.close()
    raise SiteCrawlError(f"Falha na requisição HTTPS: {type(last_error).__name__ if last_error else 'erro desconhecido'}.")


def crawl_authorized_site(
    target: str,
    *,
    allowed_hosts: set[str] | frozenset[str],
    max_pages: int = 10,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Crawl a small number of same-host HTML pages without following redirects."""
    try:
        hostname = require_in_scope(target, allowed_hosts)
    except ScopeError as exc:
        raise SiteCrawlError(str(exc)) from exc
    hostname = _validate_hostname(hostname)
    if isinstance(max_pages, bool) or not isinstance(max_pages, int) or not 1 <= max_pages <= MAX_PAGES:
        raise SiteCrawlError(f"max_pages deve ficar entre 1 e {MAX_PAGES}.")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout <= MAX_TIMEOUT_SECONDS:
        raise SiteCrawlError(f"timeout deve ser maior que zero e no máximo {MAX_TIMEOUT_SECONDS:g} segundos.")

    base = f"https://{hostname}/"
    pending = [base]
    seen: set[str] = set()
    pages: list[dict[str, Any]] = []
    issues: list[dict[str, str]] = []
    technology_hints: dict[str, set[str]] = {key: set() for key in TECHNOLOGY_HEADERS}

    while pending and len(pages) < max_pages:
        url = pending.pop(0)
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname != hostname or parsed.port not in (None, 443):
            continue
        normalized = urlunsplit(("https", hostname, parsed.path or "/", parsed.query, ""))
        if normalized in seen:
            continue
        seen.add(normalized)
        path = (parsed.path or "/")
        if parsed.query:
            path += "?" + parsed.query
        try:
            response = _request(hostname, path, float(timeout))
        except SiteCrawlError as exc:
            issues.append({"url": normalized, "error": str(exc)})
            continue

        headers = response["headers"]
        for name in TECHNOLOGY_HEADERS:
            value = headers.get(name)
            if value:
                technology_hints[name].add(value[:200])
        missing_headers = [name for name in SECURITY_HEADERS if name not in headers]
        page: dict[str, Any] = {
            "url": normalized,
            "http_status": response["status"],
            "content_type": headers.get("content-type"),
            "redirect_followed": False,
            "body_truncated": bool(response.get("truncated", False)),
            "security_headers": {
                name: {"present": name in headers, "value": headers.get(name)}
                for name in SECURITY_HEADERS
            },
            "missing_security_headers": missing_headers,
        }
        body = response["body"]
        if body and not response["redirect"]:
            charset = "utf-8"
            try:
                text_body = body.decode(charset, errors="replace")
            except Exception:
                text_body = ""
            parser = _Links()
            try:
                parser.feed(text_body)
            except Exception:
                pass
            page["title"] = " ".join(" ".join(parser.title_parts).split())[:300]
            pages.append(page)
            for href in parser.links:
                if len(pending) >= MAX_PAGES * 4:
                    break
                candidate = urlsplit(urljoin(normalized, href.strip()))
                if candidate.scheme.lower() != "https" or candidate.hostname != hostname:
                    continue
                if candidate.username or candidate.password or candidate.port not in (None, 443):
                    continue
                if candidate.fragment:
                    candidate = candidate._replace(fragment="")
                candidate_url = urlunsplit(("https", hostname, candidate.path or "/", candidate.query, ""))
                if candidate_url not in seen and candidate_url not in pending:
                    pending.append(candidate_url)
        else:
            pages.append(page)

    return {
        "target": hostname,
        "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "source": "authorized-same-host-site-crawl",
        "pages_requested": len(seen),
        "pages_analyzed": len(pages),
        "max_pages": max_pages,
        "technology_hints": {k: sorted(v) for k, v in technology_hints.items()},
        "pages": pages,
        "request_errors": issues,
        "notes": [
            "Rastreamento limitado a páginas HTTPS do hostname autorizado exato.",
            "GET de leitura apenas; não envia formulários, não executa JavaScript e não explora vulnerabilidades.",
            "Redirecionamentos não são seguidos; links externos são ignorados.",
            "Cabeçalhos ausentes e versões expostas são indicadores para revisão, não confirmação isolada de vulnerabilidade.",
        ],
    }
