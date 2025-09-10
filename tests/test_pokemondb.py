import logging

import pytest

from pogorarity.sources import pokemondb


class DummyResponse:
    def __init__(self, text: str):
        self.text = text


def test_pokemondb_scaling(monkeypatch, caplog):
    html = "<table><tr><th>Catch rate</th><td>300</td></tr></table>"
    monkeypatch.setattr(
        pokemondb,
        "safe_request",
        lambda url, session=None, metrics=None: DummyResponse(html),
    )
    monkeypatch.setattr(
        "pogorarity.aggregator.get_comprehensive_pokemon_list",
        lambda: [("Pidgey", 1)],
    )
    with caplog.at_level(logging.WARNING):
        data, report = pokemondb.scrape_catch_rate(limit=1)
    assert report.success
    assert data["Pidgey"] == pytest.approx(10.0)
    assert "outside expected range" in caplog.text
