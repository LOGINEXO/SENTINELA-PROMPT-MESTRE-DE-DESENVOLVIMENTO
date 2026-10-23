"""Offline tests for the NVD public intelligence client."""
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from sentinela.intelligence.nvd import NVDClientError, get_cve, normalize_cve, search_cves


def sample_cve():
    return {
        "id": "CVE-2025-12345", "published": "2025-01-01T00:00:00.000",
        "lastModified": "2025-01-02T00:00:00.000", "vulnStatus": "Analyzed",
        "descriptions": [{"lang": "en", "value": "Example vulnerability."}],
        "metrics": {"cvssMetricV31": [{"cvssData": {
            "version": "3.1", "baseScore": 8.8, "baseSeverity": "HIGH",
            "vectorString": "CVSS:3.1/example"}}]},
        "configurations": [{"nodes": [{"cpeMatch": [{
            "criteria": "cpe:2.3:a:vendor:product:1.2:*:*:*:*:*:*:*",
            "vulnerable": True, "versionEndExcluding": "1.2.5"}]}]}],
        "references": [{"url": "https://example.test/advisory", "tags": ["Vendor Advisory"]}],
    }


def api_response(cves):
    return {"resultsPerPage": len(cves), "startIndex": 0,
            "totalResults": len(cves), "vulnerabilities": [{"cve": c} for c in cves]}


class FakeResponse:
    def __init__(self, payload): self.payload = payload
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return self.payload


class NVDTests(unittest.TestCase):
    @patch("sentinela.intelligence.nvd.urlopen")
    def test_search_normalizes_and_sends_bounded_request(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse(json.dumps(api_response([sample_cve()])).encode())
        results = search_cves(" product ", limit=3, api_key="test-key")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["cve_id"], "CVE-2025-12345")
        self.assertEqual(results[0]["cvss"]["base_score"], 8.8)
        self.assertEqual(results[0]["affected_products"][0]["vendor"], "vendor")
        self.assertFalse(results[0]["asset_confirmed"])
        request = mock_urlopen.call_args.args[0]
        self.assertIn("keywordSearch=product", request.full_url)
        self.assertEqual(request.get_header("Apikey"), "test-key")

    @patch("sentinela.intelligence.nvd.urlopen")
    def test_deduplicates_cve_ids(self, mock_urlopen):
        cve = sample_cve()
        mock_urlopen.return_value = FakeResponse(json.dumps(api_response([cve, cve])).encode())
        self.assertEqual(len(search_cves("test")), 1)

    @patch("sentinela.intelligence.nvd.urlopen")
    def test_get_cve_returns_record(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse(json.dumps(api_response([sample_cve()])).encode())
        self.assertEqual(get_cve("cve-2025-12345")["cve_id"], "CVE-2025-12345")

    @patch("sentinela.intelligence.nvd.urlopen")
    def test_get_cve_returns_none_when_missing(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse(json.dumps(api_response([])).encode())
        self.assertIsNone(get_cve("CVE-2025-12345"))

    def test_rejects_invalid_input_and_limits(self):
        with self.assertRaises(ValueError): search_cves("  ")
        with self.assertRaises(ValueError): search_cves("x", limit=0)
        with self.assertRaises(ValueError): search_cves("x", limit=101)
        with self.assertRaises(ValueError): get_cve("not-a-cve")

    @patch("sentinela.intelligence.nvd.urlopen", side_effect=HTTPError("url", 429, "limited", {}, None))
    def test_rate_limit_has_clear_error(self, _mock):
        with self.assertRaisesRegex(NVDClientError, "429"): search_cves("test")

    @patch("sentinela.intelligence.nvd.urlopen", side_effect=URLError("offline"))
    def test_network_failure_is_wrapped(self, _mock):
        with self.assertRaisesRegex(NVDClientError, "rede"): search_cves("test")

    @patch("sentinela.intelligence.nvd.urlopen")
    def test_invalid_json_is_rejected(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse(b"not-json")
        with self.assertRaisesRegex(NVDClientError, "JSON UTF-8"): search_cves("test")

    @patch("sentinela.intelligence.nvd.urlopen")
    def test_invalid_payload_is_rejected(self, mock_urlopen):
        mock_urlopen.return_value = FakeResponse(b"{}")
        with self.assertRaisesRegex(NVDClientError, "vulnerabilities"): search_cves("test")

    def test_rejects_non_finite_timeout(self):
        with self.assertRaises(ValueError): search_cves("test", timeout=float("nan"))
        with self.assertRaises(ValueError): search_cves("test", timeout=float("inf"))

    def test_normalization_handles_missing_optional_fields(self):
        result = normalize_cve({"id": "CVE-2024-1111", "descriptions": []})
        self.assertEqual(result["description"], "")
        self.assertIsNone(result["cvss"])
        self.assertEqual(result["affected_products"], [])
        self.assertEqual(result["references"], [])


if __name__ == "__main__":
    unittest.main()
