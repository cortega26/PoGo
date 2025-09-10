import logging
import pytest

from pogorarity.sources import game_master


class DummyResponse:
    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data


def test_game_master_parsing(monkeypatch, caplog):
    sample_data = [
        {
            "templateId": "V0001_POKEMON_BULBASAUR",
            "data": {
                "pokemonSettings": {
                    "pokemonId": "BULBASAUR",
                    "encounter": {"base_capture_rate": 0.2},
                    "spawnWeight": 50,
                }
            },
        },
        {
            "templateId": "V0004_POKEMON_CHARMANDER",
            "data": {
                "pokemonSettings": {
                    "pokemonId": "CHARMANDER",
                    "encounter": {"base_capture_rate": 1.5},
                    "spawnWeight": 25,
                }
            },
        },
        {
            "templateId": "V0007_POKEMON_SQUIRTLE",
            "data": {
                "pokemonSettings": {
                    "pokemonId": "SQUIRTLE",
                    "encounter": {"base_capture_rate": 0.1},
                    "spawnWeight": -5,
                }
            },
        },
    ]

    monkeypatch.setattr(
        game_master,
        "safe_request",
        lambda url, metrics=None: DummyResponse(sample_data),
    )
    with caplog.at_level(logging.WARNING):
        capture, spawn, reports = game_master.scrape()
    assert capture["Bulbasaur"] == pytest.approx(2.0)
    assert capture["Charmander"] == pytest.approx(10.0)
    assert capture["Squirtle"] == pytest.approx(1.0)
    assert spawn["Bulbasaur"] == pytest.approx(10.0)
    assert spawn["Charmander"] == pytest.approx(5.0)
    assert spawn["Squirtle"] == pytest.approx(0.0)
    assert reports[0].success
    assert reports[1].success
    assert "outside expected range" in caplog.text
