import json

import requests

from pogorarity import EnhancedRarityScraper


class DummyResponse:
    status_code = 200

    def raise_for_status(self):
        pass


def test_safe_request_retries_with_backoff(monkeypatch):
    scraper = EnhancedRarityScraper()

    calls = {"count": 0}

    def fake_get(url, timeout):
        if calls["count"] == 0:
            calls["count"] += 1
            raise requests.RequestException("boom")
        return DummyResponse()

    sleeps = []
    monkeypatch.setattr(scraper.session, "get", fake_get)
    monkeypatch.setattr("pogorarity.scraper.time.sleep", lambda s: sleeps.append(s))
    monkeypatch.setattr("pogorarity.scraper.random.uniform", lambda a, b: 0)
    scraper.delay = 1

    response = scraper.safe_request("http://example.com", retries=2)

    assert response.status_code == 200
    assert sleeps == [1]


def test_safe_request_logs_json(monkeypatch, caplog):
    scraper = EnhancedRarityScraper()

    monkeypatch.setattr(scraper.session, "get", lambda url, timeout: DummyResponse())
    monkeypatch.setattr("pogorarity.scraper.random.uniform", lambda a, b: 0)

    with caplog.at_level("INFO"):
        scraper.safe_request("http://example.com", retries=1)

    log = caplog.records[0].msg
    data = json.loads(log)
    assert data["url"] == "http://example.com"
    assert data["status"] == 200
