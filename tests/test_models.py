import pytest
from pydantic import ValidationError

from pogorarity.models import DataSourceReport, PokemonRarity


def test_pokemon_rarity_validation():
    pokemon = PokemonRarity(
        name="Bulbasaur",
        number=1,
        rarity_scores={"source": 1.0},
        average_score=1.0,
        recommendation="Keep",
        data_sources=["source"],
        spawn_type="wild",
    )
    assert pokemon.number == 1

    with pytest.raises(ValidationError):
        PokemonRarity(
            name="Charmander",
            number="not-a-number",
            rarity_scores={},
            average_score=1.0,
            recommendation="Keep",
            data_sources=[],
            spawn_type="wild",
        )


def test_datasource_report_validation():
    with pytest.raises(ValidationError):
        DataSourceReport(source_name="site", pokemon_count="ten", success=True)
