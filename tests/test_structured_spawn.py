import logging

import pytest

from pogorarity.sources import structured_spawn


class DummyResponse:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data


def test_structured_spawn_scaling(monkeypatch, caplog):
    sample = {
        "pokemon": [
            {"name": "Pikachu", "spawn_chance": 5},
            {"name": "Mewtwo", "spawn_chance": 25},
        ]
    }
    monkeypatch.setattr(
        structured_spawn,
        "safe_request",
        lambda url, metrics=None: DummyResponse(sample),
    )
    with caplog.at_level(logging.WARNING):
        data, report = structured_spawn.scrape()
    assert report.success
    assert data["Pikachu"] == pytest.approx(2.5)
    assert data["Mewtwo"] == 10.0
    assert "outside expected range" in caplog.text
