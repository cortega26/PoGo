import pytest

from pogorarity.normalizer import normalize_encounters, Rarity


def test_normalization_schema_and_duplicates():
    raw = [
        {"pokemon_name": "Pikachu", "rarity": "Common", "extra": 1},
        {"pokemon_name": "Pikachu", "rarity": "Common"},  # duplicate
        {"pokemon_name": "Rattata", "form": "Alolan", "rarity": 2},
        {"pokemon_name": "Rattata", "rarity": 7},
        {"pokemon_name": "Mew", "rarity": "Legendary"},
        {"pokemon_name": "MissingNo", "rarity": "Unknown"},  # invalid
    ]
    normalized, errors = normalize_encounters(raw)
    assert [r.model_dump() for r in normalized] == [
        {
            "pokemon_name": "Pikachu",
            "rarity": Rarity.common,
            "spawn_rate": None,
            "source": None,
            "form": None,
        },
        {
            "pokemon_name": "Rattata",
            "rarity": Rarity.rare,
            "spawn_rate": None,
            "source": None,
            "form": "Alolan",
        },
        {
            "pokemon_name": "Rattata",
            "rarity": Rarity.common,
            "spawn_rate": None,
            "source": None,
            "form": None,
        },
        {
            "pokemon_name": "Mew",
            "rarity": Rarity.legendary,
            "spawn_rate": None,
            "source": None,
            "form": None,
        },
    ]
    assert len(errors) == 1


def test_spawn_rate_percentage_validation():
    raw = [
        {"pokemon_name": "Charmander", "rarity": "Common", "spawn_rate": "10%"},
        {"pokemon_name": "Squirtle", "rarity": "Common", "spawn_rate": "10"},
    ]
    normalized, errors = normalize_encounters(raw)
    assert [r.model_dump() for r in normalized] == [
        {
            "pokemon_name": "Charmander",
            "rarity": Rarity.common,
            "spawn_rate": 0.10,
            "source": None,
            "form": None,
        }
    ]
    assert len(errors) == 1
