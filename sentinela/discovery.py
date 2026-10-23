"""Discover candidate websites from a keyword using public search results only.

This module does not connect to discovered websites or test them. Results are
untrusted leads and must be reviewed before any authorized-site audit.
"""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
import json
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlsplit, unquote
from urllib.request import Request, urlopen

MAX_QUERY_LENGTH = 120
MAX_RESULTS = 10
_TIMEOUT = 8


class _Results(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.items: list[dict[str, str]] = []
        self._capture = False
        self._href = ""
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "a" and "result__a" in (attrs_dict.get("class") or "").split():
            self._capture = True
            self._href = attrs_dict.get("href") or ""
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._capture:
            title = " ".join(" ".join(self._text).split())[:240]
            url = self._candidate_url(self._href)
            if url and title and len(self.items) < MAX_RESULTS:
                self.items.append({"title": title, "url": url, "hostname": urlsplit(url).hostname or ""})
            self._capture = False

    @staticmethod
    def _candidate_url(raw: str) -> str | None:
        if not raw or len(raw) > 4096:
            return None
        parsed = urlsplit(raw)
        if parsed.path.startswith("/l/") or "duckduckgo.com" in (parsed.hostname or ""):
            wrapped = parse_qs(parsed.query).get("uddg", [])
            if wrapped:
                raw = unquote(wrapped[0])
                parsed = urlsplit(raw)
        if parsed.scheme.lower() not in ("http", "https") or not parsed.hostname:
            return None
        if parsed.username or parsed.password or parsed.port not in (None, 80, 443):
            return None
        host = parsed.hostname.lower().rstrip(".")
        if "." not in host or len(host) > 253 or re.fullmatch(r"[0-9.]+", host):
            return None
        if any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label) for label in host.split(".")):
            return None
        return f"{parsed.scheme.lower()}://{host}/"


def discover_sites(query: str, *, limit: int = 10) -> dict:
    """Return candidate links from DuckDuckGo HTML search without probing targets."""
    if not isinstance(query, str) or not query.strip() or len(query.strip()) > MAX_QUERY_LENGTH:
        raise ValueError(f"Informe uma palavra-chave de até {MAX_QUERY_LENGTH} caracteres.")
    if any(ord(c) < 32 or ord(c) == 127 for c in query):
        raise ValueError("A palavra-chave contém caracteres de controle.")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_RESULTS:
        raise ValueError(f"O limite deve ficar entre 1 e {MAX_RESULTS}.")
    endpoint = "https://html.duckduckgo.com/html/?" + urlencode({"q": query.strip()})
    request = Request(endpoint, headers={"User-Agent": "Sentinela/0.5 (public-search-discovery)", "Accept": "text/html"})
    try:
        with urlopen(request, timeout=_TIMEOUT) as response:
            if response.status != 200:
                raise ValueError(f"Pesquisa pública retornou HTTP {response.status}.")
            body = response.read(1_000_000 + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise ValueError(f"Não foi possível consultar a pesquisa pública: {type(exc).__name__}.") from exc
    if len(body) > 1_000_000:
        raise ValueError("Resposta da pesquisa ultrapassou o limite permitido.")
    parser = _Results()
    parser.feed(body.decode("utf-8", errors="replace"))
    unique: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in parser.items:
        host = item["hostname"]
        if host not in seen:
            unique.append(item)
            seen.add(host)
        if len(unique) >= limit:
            break
    return {
        "query": query.strip(),
        "source": "DuckDuckGo HTML public search",
        "candidate_count": len(unique),
        "candidates": unique,
        "important": "Somente resultados de pesquisa pública. Nenhum site encontrado foi acessado ou testado. Confirme a propriedade/autorização antes de executar auditorias.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Descobre sites candidatos por palavra-chave; não testa os sites.")
    parser.add_argument("--query", required=True)
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args(argv)
    try:
        result = discover_sites(args.query, limit=args.limit)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
