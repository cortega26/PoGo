import json

import json
import requests

from pogorarity.helpers import safe_request


class DummyResponse:
    status_code = 200

    def raise_for_status(self):
        pass


def test_safe_request_retries_with_backoff(monkeypatch):
    session = requests.Session()

    calls = {"count": 0}

    def fake_get(url, timeout):
        if calls["count"] == 0:
            calls["count"] += 1
            raise requests.RequestException("boom")
        return DummyResponse()

    sleeps = []
    monkeypatch.setattr(session, "get", fake_get)
    monkeypatch.setattr("pogorarity.helpers.time.sleep", lambda s: sleeps.append(s))
    monkeypatch.setattr("pogorarity.helpers.random.uniform", lambda a, b: 0)

    response = safe_request("http://example.com", retries=2, session=session, delay=1)

    assert response.status_code == 200
    assert sleeps == [1]


def test_safe_request_logs_json(monkeypatch, caplog):
    session = requests.Session()

    monkeypatch.setattr(session, "get", lambda url, timeout: DummyResponse())
    monkeypatch.setattr("pogorarity.helpers.random.uniform", lambda a, b: 0)

    with caplog.at_level("INFO"):
        safe_request("http://example.com", retries=1, session=session)

    log = caplog.records[0].msg
    data = json.loads(log)
    assert data["url"] == "http://example.com"
    assert data["status"] == 200
