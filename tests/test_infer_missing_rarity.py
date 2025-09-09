import pytest
from pogorarity.aggregator import infer_missing_rarity


@pytest.mark.parametrize(
    "name,number,spawn_type,expected",
    [
        ("Dratini", 147, "wild", 1.5),  # pseudo-legendary rule
        ("Bulbasaur", 1, "wild", 6.0),  # starter rule
        ("Pidgey", 16, "wild", 8.5),  # very common rule
        ("Alolan Vulpix", 37, "wild", 4.0),  # regional form rule
        ("Zigzagoon", 263, "wild", 5.0),  # generation-based default
    ],
)
def test_infer_missing_rarity(name, number, spawn_type, expected):
    assert infer_missing_rarity(name, number, spawn_type) == expected
