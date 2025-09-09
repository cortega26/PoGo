import pandas as pd
import pytest

from pogorarity.normalizer import canonicalize_name, lookup_number
from pogorarity.scraper import EnhancedRarityScraper
from pogorarity.models import DataSourceReport


def test_canonicalize_name_starters():
    cases = [
        ("Balbusaur", "Bulbasaur", 1),
        ("Charmender", "Charmander", 4),
        ("Squitle", "Squirtle", 7),
    ]
    for raw, expected_name, expected_number in cases:
        assert canonicalize_name(raw) == expected_name
        assert lookup_number(raw) == expected_number


def test_merge_integrity_and_aggregation(monkeypatch):
    scraper = EnhancedRarityScraper()

    # limit pokemon list to three starters
    monkeypatch.setattr(
        scraper,
        "get_comprehensive_pokemon_list",
        lambda: [("Bulbasaur", 1), ("Charmander", 4), ("Squirtle", 7)],
    )

    # patched data sources
    monkeypatch.setattr(
        scraper,
        "scrape_structured_spawn_data",
        lambda: ({1: 0.3, 4: 0.2, 7: 0.25}, DataSourceReport(source_name="Structured", pokemon_count=3, success=True)),
    )
    monkeypatch.setattr(
        scraper,
        "get_curated_spawn_data",
        lambda: ({1: 6.0, 4: 6.0, 7: 6.0}, DataSourceReport(source_name="Curated", pokemon_count=3, success=True)),
    )
    monkeypatch.setattr(
        scraper,
        "scrape_pokemondb_catch_rate",
        lambda limit=None: ({1: 1.76, 4: 1.76, 7: 1.76}, DataSourceReport(source_name="Catch", pokemon_count=3, success=True)),
    )
    monkeypatch.setattr(
        scraper,
        "categorize_pokemon_spawn_type",
        lambda name, number: "wild",
    )

    results = scraper.aggregate_data()

    # join key integrity: merged frame contains exactly the three IDs
    merged = scraper.intermediate_frames["merged"]
    assert set(merged["number"]) == {1, 4, 7}
    assert merged["number"].is_unique

    # aggregation spot check
    bulba = next(p for p in results if p.name == "Bulbasaur")
    assert bulba.average_score == pytest.approx(6.0)
