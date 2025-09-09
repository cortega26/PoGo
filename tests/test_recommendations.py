import json
import pytest
from pogorarity import get_trading_recommendation, categorize_pokemon_spawn_type


@pytest.mark.parametrize(
    "score,spawn_type,expected",
    [
        (5.0, "legendary", "Never Transfer (Legendary)"),
        (5.0, "event-only", "Never Transfer (Event Only)"),
        (5.0, "evolution-only", "Evaluate for Evolution"),
        (3.99, "wild", "Keep or Trade Sparingly"),
        (4.0, "wild", "Depends on Circumstances"),
        (6.99, "wild", "Depends on Circumstances"),
        (7.0, "wild", "Safe to Transfer"),
    ],
)
def test_get_trading_recommendation(score, spawn_type, expected):
    assert get_trading_recommendation(score, spawn_type) == expected


@pytest.fixture
def spawn_types_file(tmp_path):
    mapping = {
        "Mewtwo": "legendary",
        "Ivysaur": "evolution-only",
        "Smeargle": "event-only",
    }
    path = tmp_path / "spawn_types.json"
    path.write_text(json.dumps(mapping))
    return path


@pytest.mark.parametrize(
    "name,number,expected",
    [
        ("Mewtwo", 150, "legendary"),
        ("Ivysaur", 2, "evolution-only"),
        ("Smeargle", 235, "event-only"),
        ("Pikachu", 25, "wild"),
    ],
)
def test_categorize_pokemon_spawn_type(spawn_types_file, name, number, expected):
    assert categorize_pokemon_spawn_type(name, number, spawn_types_file) == expected

