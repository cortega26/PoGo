import logging
import pytest

from pogorarity.sources import silph_road


class DummyResponse:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data


def test_silph_road_mapping(monkeypatch, caplog):
    sample_data = [
        {"name": "Bulbasaur", "tier": 1},
        {"name": "Mewtwo", "tier": 7},
    ]
    monkeypatch.setattr(
        silph_road,
        "safe_request",
        lambda url, session=None, metrics=None: DummyResponse(sample_data),
    )
    with caplog.at_level(logging.WARNING):
        data, report = silph_road.scrape_spawn_tiers()
    assert report.success
    assert data["Bulbasaur"] == pytest.approx(10.0)
    assert data["Mewtwo"] == pytest.approx(0.0)
    assert "outside expected range" in caplog.text
