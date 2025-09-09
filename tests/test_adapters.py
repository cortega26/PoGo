from datetime import datetime
import json

from pogorarity.adapters import (
    parse_go_hub,
    parse_pokemondb_page,
    parse_structured_spawn_data,
)


def test_parse_structured_spawn_data():
    sample = {
        "pokemon": [
            {"name": "Bulbasaur", "spawn_chance": 0.69},
            {"name": "Mewtwo", "spawn_chance": 0.0005},
        ]
    }
    records = parse_structured_spawn_data(json.dumps(sample), timestamp=datetime(2024, 1, 1))
    assert records[0].pokemon_name == "Bulbasaur"
    assert records[0].source == "Structured Spawn Data"


def test_parse_pokemondb_page():
    html = """<table><tr><th>Catch rate</th><td>45 (test)</td></tr></table>"""
    rec = parse_pokemondb_page("Bulbasaur", html, timestamp=datetime(2024, 1, 1))
    assert rec is not None
    assert rec.pokemon_name == "Bulbasaur"
    assert rec.source == "PokemonDB Catch Rate"


def test_parse_go_hub():
    html = """<table><tr><td>Bulbasaur</td><td>Common</td></tr></table>"""
    records = parse_go_hub(html, timestamp=datetime(2024, 1, 1))
    assert records and records[0].rarity == 8.0
    assert records[0].source == "Pokemon GO Hub"
