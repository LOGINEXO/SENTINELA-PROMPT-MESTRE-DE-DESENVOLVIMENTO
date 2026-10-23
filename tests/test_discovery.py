from sentinela.discovery import _Results, discover_sites
import pytest


def test_candidate_url_accepts_http_and_https_domains_only():
    assert _Results._candidate_url("https://example.com/path?q=1") == "https://example.com/"
    assert _Results._candidate_url("http://sub.example.com/") == "http://sub.example.com/"
    assert _Results._candidate_url("javascript:alert(1)") is None
    assert _Results._candidate_url("http://127.0.0.1/") is None
    assert _Results._candidate_url("http://localhost/") is None
    assert _Results._candidate_url("https://user:pass@example.com/") is None
    assert _Results._candidate_url("https://example.com:8443/") is None


def test_parser_extracts_search_result_candidates():
    parser = _Results()
    parser.feed('<a class="result__a" href="https://example.com/path">Example site</a>')
    assert parser.items == [{"title": "Example site", "url": "https://example.com/", "hostname": "example.com"}]


@pytest.mark.parametrize("query,limit", [("", 5), ("x" * 121, 5), ("bank", 0), ("bank", 11)])
def test_discovery_validates_query_and_result_limit_without_network(query, limit):
    with pytest.raises(ValueError):
        discover_sites(query, limit=limit)
