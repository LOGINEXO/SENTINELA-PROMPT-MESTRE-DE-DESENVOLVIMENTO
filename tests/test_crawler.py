from sentinela.audit import crawler


def test_crawl_analyzes_same_host_pages_without_following_external_links(monkeypatch):
    monkeypatch.setattr(crawler, "_resolve_public_addresses", lambda host: ["93.184.216.34"])
    monkeypatch.setattr(crawler, "_validate_hostname", lambda host: host)
    monkeypatch.setattr(crawler, "require_in_scope", lambda target, allowed: target)

    html = b"""<html><head><title>Home</title></head><body>
    <a href="/about">About</a><a href="https://outside.example/">External</a>
    </body></html>"""

    def fake_request(hostname, path, timeout):
        assert hostname == "example.com"
        if path == "/":
            return {"status": 200, "headers": {"content-type": "text/html"}, "body": html, "redirect": False}
        return {"status": 200, "headers": {"content-type": "text/html", "content-security-policy": "default-src 'self'"},
                "body": b"<html><title>About</title></html>", "redirect": False}

    monkeypatch.setattr(crawler, "_request", fake_request)
    result = crawler.crawl_authorized_site("example.com", allowed_hosts={"example.com"}, max_pages=5)
    assert result["pages_analyzed"] == 2
    assert result["pages"][0]["title"] == "Home"
    assert all("outside.example" not in page["url"] for page in result["pages"])
    assert result["pages"][0]["missing_security_headers"]


def test_crawl_rejects_page_limit_out_of_range(monkeypatch):
    monkeypatch.setattr(crawler, "_validate_hostname", lambda host: host)
    monkeypatch.setattr(crawler, "require_in_scope", lambda target, allowed: target)
    try:
        crawler.crawl_authorized_site("example.com", allowed_hosts={"example.com"}, max_pages=26)
    except crawler.SiteCrawlError as exc:
        assert "1 e 25" in str(exc)
    else:
        raise AssertionError("Expected SiteCrawlError")
