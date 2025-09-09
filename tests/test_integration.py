import pytest

from pogorarity.aggregator import aggregate_data
from pogorarity.models import DataSourceReport
from pogorarity.sources import curated_spawn, pokemondb, structured_spawn, pokeapi

def test_pokemondb_integration_small_set():
    data, report = pokemondb.scrape_catch_rate(limit=2)
    assert report.success
    assert len(data) == 2


def test_pokeapi_integration_small_set():
    data, report = pokeapi.scrape_capture_rate(limit=2)
    assert report.success
    assert len(data) == 2


def test_weighted_aggregation(monkeypatch):
    """Ensure aggregate_data uses weighted averages from multiple sources."""
    # Use a tiny deterministic dataset to avoid network access.
    monkeypatch.setattr(
        "pogorarity.aggregator.get_comprehensive_pokemon_list",
        lambda: [("Bulbasaur", 1)],
    )
    monkeypatch.setattr(
        "pogorarity.aggregator.categorize_pokemon_spawn_type",
        lambda name, num: "wild",
    )

    def fake_structured():
        return ({'Bulbasaur': 2.0}, DataSourceReport(
            source_name='Structured Spawn Data', pokemon_count=1, success=True))

    def fake_curated():
        return ({'Bulbasaur': 4.0}, DataSourceReport(
            source_name='Enhanced Curated Data', pokemon_count=1, success=True))

    def fake_pokemondb(limit=None):
        return ({'Bulbasaur': 6.0}, DataSourceReport(
            source_name='PokemonDB Catch Rate', pokemon_count=1, success=True))

    def fake_pokeapi(limit=None, session=None, metrics=None):
        return ({'Bulbasaur': 8.0}, DataSourceReport(
            source_name='PokeAPI Capture Rate', pokemon_count=1, success=True))

    monkeypatch.setattr(structured_spawn, 'scrape', lambda metrics=None: fake_structured())
    monkeypatch.setattr(curated_spawn, 'get_data', lambda: fake_curated())
    monkeypatch.setattr(pokemondb, 'scrape_catch_rate', lambda limit=None, session=None, metrics=None: fake_pokemondb())
    monkeypatch.setattr(pokeapi, 'scrape_capture_rate', lambda limit=None, session=None, metrics=None: fake_pokeapi())

    results, _ = aggregate_data(limit=1)
    assert len(results) == 1
    assert results[0].average_score == pytest.approx(5.6666667)
