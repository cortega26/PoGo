import pytest

from pogorarity.normalizer import normalize_encounters, Rarity


def test_normalization_schema_and_duplicates():
    raw = [
        {"pokemon_name": "Pikachu", "rarity": "Common", "extra": 1},
        {"pokemon_name": "Pikachu", "rarity": "Common"},  # duplicate
        {"pokemon_name": "Mew", "rarity": "Legendary"},
        {"pokemon_name": "MissingNo", "rarity": "Unknown"},  # invalid
    ]
    normalized, errors = normalize_encounters(raw)
    assert [r.model_dump() for r in normalized] == [
        {"pokemon_name": "Pikachu", "rarity": Rarity.common, "spawn_rate": None, "source": None},
        {"pokemon_name": "Mew", "rarity": Rarity.legendary, "spawn_rate": None, "source": None},
    ]
    assert len(errors) == 1
