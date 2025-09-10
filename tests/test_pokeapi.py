import logging
import pytest

from pogorarity.sources import pokeapi


class DummyResponse:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data


def test_pokeapi_normalization(monkeypatch, caplog):
    monkeypatch.setattr(
        "pogorarity.aggregator.get_comprehensive_pokemon_list",
        lambda: [("Bulbasaur", 1)],
    )
    monkeypatch.setattr(
        pokeapi,
        "safe_request",
        lambda url, session=None, metrics=None: DummyResponse({"capture_rate": 300}),
    )

    with caplog.at_level(logging.WARNING):
        data, report = pokeapi.scrape_capture_rate(limit=1)
    assert report.success
    assert data["Bulbasaur"] == pytest.approx(10.0)
    assert "outside expected range" in caplog.text
