import pytest

from pogorarity import EnhancedRarityScraper, DataSourceReport

def test_pokemondb_integration_small_set():
    scraper = EnhancedRarityScraper()
    data, report = scraper.scrape_pokemondb_catch_rate(limit=2)
    assert report.success
    assert len(data) == 2


def test_weighted_aggregation(monkeypatch):
    """Ensure aggregate_data uses weighted averages from multiple sources."""
    scraper = EnhancedRarityScraper()
    scraper.scrape_limit = 1

    # Use a tiny deterministic dataset to avoid network access.
    monkeypatch.setattr(
        scraper, 'get_comprehensive_pokemon_list',
        lambda: [('Bulbasaur', 1)]
    )
    monkeypatch.setattr(
        scraper, 'categorize_pokemon_spawn_type',
        lambda name, num: 'wild'
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

    monkeypatch.setattr(scraper, 'scrape_structured_spawn_data', fake_structured)
    monkeypatch.setattr(scraper, 'get_curated_spawn_data', fake_curated)
    monkeypatch.setattr(scraper, 'scrape_pokemondb_catch_rate', fake_pokemondb)

    results = scraper.aggregate_data()
    assert len(results) == 1
    assert results[0].average_score == pytest.approx(4.5)
