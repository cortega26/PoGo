from pathlib import Path
from pogorarity import EnhancedRarityScraper

def test_parse_catch_rate_from_fixture():
    scraper = EnhancedRarityScraper()
    fixture = Path(__file__).parent / "fixtures" / "pokemondb_bulbasaur.html"
    html = fixture.read_text(encoding="utf-8")
    catch_rate = scraper.parse_pokemondb_catch_rate(html)
    assert catch_rate == 45
