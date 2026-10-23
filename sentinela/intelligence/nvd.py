"""Small, bounded client for the official NVD CVE API 2.0.

This module retrieves public vulnerability metadata only. It never contacts
assets mentioned by CVE records or performs security tests against them.
"""
from __future__ import annotations

import json
from math import isfinite
import os
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
DEFAULT_TIMEOUT_SECONDS = 10
MAX_RESULTS = 100
_CVE_ID = re.compile(r"^CVE-\d{4}-\d{4,}$", re.IGNORECASE)


class NVDClientError(RuntimeError):
    """Raised when the NVD API cannot return a usable response."""


def search_cves(keyword: str, *, limit: int = 20, api_key: str | None = None,
                timeout: float = DEFAULT_TIMEOUT_SECONDS) -> list[dict[str, Any]]:
    """Search NVD by keyword and return normalized, deduplicated CVEs."""
    keyword = keyword.strip() if isinstance(keyword, str) else ""
    if not keyword:
        raise ValueError("A busca NVD exige uma palavra-chave não vazia.")
    if len(keyword) > 200:
        raise ValueError("A palavra-chave deve ter no máximo 200 caracteres.")
    return _query({"keywordSearch": keyword}, limit=limit, api_key=api_key, timeout=timeout)


def get_cve(cve_id: str, *, api_key: str | None = None,
            timeout: float = DEFAULT_TIMEOUT_SECONDS) -> dict[str, Any] | None:
    """Fetch one CVE by identifier, or return None when it is not found."""
    cve_id = cve_id.strip().upper() if isinstance(cve_id, str) else ""
    if not _CVE_ID.fullmatch(cve_id):
        raise ValueError("Identificador inválido. Use o formato CVE-AAAA-NNNN.")
    results = _query({"cveId": cve_id}, limit=1, api_key=api_key, timeout=timeout)
    return results[0] if results else None


def _query(params: dict[str, str], *, limit: int, api_key: str | None,
           timeout: float) -> list[dict[str, Any]]:
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_RESULTS:
        raise ValueError(f"limit deve ser um inteiro entre 1 e {MAX_RESULTS}.")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout deve ser um número positivo.")
    query = urlencode({**params, "resultsPerPage": limit})
    headers = {"User-Agent": "Sentinela/0.2.0 (public vulnerability intelligence)"}
    key = api_key if api_key is not None else os.getenv("NVD_API_KEY")
    if key:
        headers["apiKey"] = key
    request = Request(f"{API_URL}?{query}", headers=headers, method="GET")
    try:
        with urlopen(request, timeout=float(timeout)) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 429:
            detail = "limite de requisições atingido (HTTP 429)"
        elif exc.code in (401, 403):
            detail = f"requisição recusada pela NVD (HTTP {exc.code})"
        else:
            detail = f"NVD respondeu HTTP {exc.code}"
        raise NVDClientError(f"Falha na consulta NVD: {detail}.") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise NVDClientError("Falha de rede ou tempo esgotado ao consultar a NVD.") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NVDClientError("A NVD retornou uma resposta que não é JSON UTF-8 válido.") from exc

    if not isinstance(payload, dict) or not isinstance(payload.get("vulnerabilities"), list):
        raise NVDClientError("Resposta NVD inválida: campo vulnerabilities ausente ou inválido.")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in payload["vulnerabilities"]:
        if not isinstance(item, dict) or not isinstance(item.get("cve"), dict):
            continue
        record = normalize_cve(item["cve"])
        if record and record["cve_id"] not in seen:
            seen.add(record["cve_id"])
            normalized.append(record)
    return normalized[:limit]


def normalize_cve(cve: dict[str, Any]) -> dict[str, Any] | None:
    """Convert an NVD CVE object to Sentinela's stable intelligence shape."""
    cve_id = cve.get("id")
    if not isinstance(cve_id, str) or not _CVE_ID.fullmatch(cve_id):
        return None
    descriptions = cve.get("descriptions")
    description = ""
    if isinstance(descriptions, list):
        description = next((d.get("value", "") for d in descriptions
                            if isinstance(d, dict) and d.get("lang") == "en"
                            and isinstance(d.get("value"), str)), "")
        if not description:
            description = next((d.get("value", "") for d in descriptions
                                if isinstance(d, dict) and isinstance(d.get("value"), str)), "")
    metrics = cve.get("metrics") if isinstance(cve.get("metrics"), dict) else {}
    return {
        "cve_id": cve_id.upper(),
        "source": "NVD",
        "published": cve.get("published"),
        "last_modified": cve.get("lastModified"),
        "status": cve.get("vulnStatus"),
        "description": description,
        "cvss": _extract_cvss(metrics),
        "affected_products": _extract_products(cve.get("configurations")),
        "references": _extract_references(cve.get("references")),
        "nvd_url": f"https://nvd.nist.gov/vuln/detail/{cve_id.upper()}",
        "validation_status": "new_public_indicator",
        "asset_confirmed": False,
    }


def _extract_cvss(metrics: dict[str, Any]) -> dict[str, Any] | None:
    for key in ("cvssMetricV40", "cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        entries = metrics.get(key)
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            data = entry.get("cvssData")
            if not isinstance(data, dict):
                continue
            return {
                "version": data.get("version"),
                "base_score": data.get("baseScore"),
                "severity": data.get("baseSeverity") or entry.get("baseSeverity"),
                "vector": data.get("vectorString"),
            }
    return None


def _extract_products(configurations: Any) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    if not isinstance(configurations, list):
        return products
    def walk(value: Any) -> None:
        if isinstance(value, list):
            for child in value:
                walk(child)
        elif isinstance(value, dict):
            matches = value.get("cpeMatch")
            if isinstance(matches, list):
                for match in matches:
                    if not isinstance(match, dict):
                        continue
                    criteria = match.get("criteria")
                    parts = criteria.split(":") if isinstance(criteria, str) else []
                    product = {
                        "criteria": criteria,
                        "vendor": parts[3] if len(parts) > 4 else None,
                        "product": parts[4] if len(parts) > 4 else None,
                        "version": parts[5] if len(parts) > 5 else None,
                        "vulnerable": match.get("vulnerable"),
                        "version_start_including": match.get("versionStartIncluding"),
                        "version_start_excluding": match.get("versionStartExcluding"),
                        "version_end_including": match.get("versionEndIncluding"),
                        "version_end_excluding": match.get("versionEndExcluding"),
                    }
                    identity = tuple(product.get(k) for k in ("criteria", "vulnerable", "version_start_including", "version_start_excluding", "version_end_including", "version_end_excluding"))
                    if identity not in seen:
                        seen.add(identity)
                        products.append(product)
            walk(value.get("nodes", []))
            walk(value.get("children", []))
    walk(configurations)
    return products


def _extract_references(references: Any) -> list[dict[str, Any]]:
    if not isinstance(references, list):
        return []
    output = []
    seen: set[str] = set()
    for ref in references:
        if not isinstance(ref, dict) or not isinstance(ref.get("url"), str):
            continue
        url = ref["url"]
        if url in seen:
            continue
        seen.add(url)
        tags = ref.get("tags")
        output.append({"url": url, "source": ref.get("source"),
                       "tags": tags if isinstance(tags, list) else []})
    return output
