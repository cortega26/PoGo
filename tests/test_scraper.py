import logging
import pytest

from scraper import scrape_structured_spawn_data, scrape_pokemondb_catch_rate


def test_structured_spawn_out_of_range(caplog):
    data = [
        {"name": "Pikachu", "spawn_chance": 5},
        {"name": "Mewtwo", "spawn_chance": 25},
    ]
    with caplog.at_level(logging.WARNING):
        result = scrape_structured_spawn_data(
            data, expected_min=0, expected_max=20, auto_scale=False
        )
    assert "outside expected range" in caplog.text
    assert result["Pikachu"] == pytest.approx(2.5)
    assert result["Mewtwo"] == 10.0


def test_structured_spawn_auto_scale(caplog):
    data = [
        {"name": "Pikachu", "spawn_chance": 5},
        {"name": "Mewtwo", "spawn_chance": 25},
    ]
    with caplog.at_level(logging.WARNING):
        result = scrape_structured_spawn_data(
            data, expected_min=0, expected_max=20, auto_scale=True
        )
    assert "outside expected range" in caplog.text
    assert result["Pikachu"] == pytest.approx(2.0)
    assert result["Mewtwo"] == pytest.approx(10.0)


def test_pokemondb_out_of_range(caplog):
    data = {"Pidgey": 300}
    with caplog.at_level(logging.WARNING):
        result = scrape_pokemondb_catch_rate(
            data, expected_min=0, expected_max=255, auto_scale=False
        )
    assert "outside expected range" in caplog.text
    assert result["Pidgey"] == 10.0
