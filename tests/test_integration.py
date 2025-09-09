from pogorarity import EnhancedRarityScraper

def test_pokemondb_integration_small_set():
    scraper = EnhancedRarityScraper()
    data, report = scraper.scrape_pokemondb_catch_rate(limit=2)
    assert report.success
    assert len(data) == 2
