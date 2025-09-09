from pathlib import Path

from pogorarity.sources.pokemondb import parse_catch_rate

def test_parse_catch_rate_from_fixture():
    fixture = Path(__file__).parent / "fixtures" / "pokemondb_bulbasaur.html"
    html = fixture.read_text(encoding="utf-8")
    catch_rate = parse_catch_rate(html)
    assert catch_rate == 45
