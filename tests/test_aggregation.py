import pytest
from unittest.mock import Mock

from pogorarity import aggregator
from pogorarity.models import DataSourceReport



def setup_common_mocks(monkeypatch, pokemon_list):
    """Patch data sources to avoid network and file access."""
    monkeypatch.setattr(
        aggregator,
        "get_comprehensive_pokemon_list",
        lambda: pokemon_list,
    )
    monkeypatch.setattr(
        aggregator,
        "categorize_pokemon_spawn_type",
        lambda name, number: "wild",
    )
    monkeypatch.setattr(
        aggregator.structured_spawn,
        "scrape",
        lambda metrics=None: (
            {},
            DataSourceReport(
                source_name="Structured Spawn Data",
                pokemon_count=0,
                success=True,
            ),
        ),
    )
    monkeypatch.setattr(
        aggregator.curated_spawn,
        "get_data",
        lambda: (
            {},
            DataSourceReport(
                source_name="Enhanced Curated Data",
                pokemon_count=0,
                success=True,
            ),
        ),
    )
    monkeypatch.setattr(
        aggregator.pokemondb,
        "scrape_catch_rate",
        lambda limit, metrics=None: (
            {},
            DataSourceReport(
                source_name="PokemonDB Catch Rate",
                pokemon_count=0,
                success=True,
            ),
        ),
    )
    monkeypatch.setattr(
        aggregator.pokeapi,
        "scrape_capture_rate",
        lambda limit, metrics=None: (
            {},
            DataSourceReport(
                source_name="PokeAPI Capture Rate",
                pokemon_count=0,
                success=True,
            ),
        ),
    )
    monkeypatch.setattr(
        aggregator.silph_road,
        "scrape_spawn_tiers",
        lambda metrics=None: (
            {},
            DataSourceReport(
                source_name="Silph Road Spawn Tier",
                pokemon_count=0,
                success=True,
            ),
        ),
    )
    monkeypatch.setattr(
        aggregator.game_master,
        "scrape",
        lambda metrics=None: (
            {},
            {},
            [
                DataSourceReport(
                    source_name="Game Master",
                    pokemon_count=0,
                    success=True,
                )
            ],
        ),
    )


def test_weighted_average_with_custom_weights(monkeypatch):
    setup_common_mocks(monkeypatch, [("Testmon", 1)])

    structured_data = {"Testmon": 4.0}
    structured_report = DataSourceReport(
        source_name="Structured Spawn Data", pokemon_count=1, success=True
    )
    monkeypatch.setattr(
        aggregator.structured_spawn,
        "scrape",
        lambda metrics=None: (structured_data, structured_report),
    )
    pokemondb_data = {"Testmon": 8.0}
    pokemondb_report = DataSourceReport(
        source_name="PokemonDB Catch Rate", pokemon_count=1, success=True
    )
    monkeypatch.setattr(
        aggregator.pokemondb,
        "scrape_catch_rate",
        lambda limit, metrics=None: (pokemondb_data, pokemondb_report),
    )

    custom_weights = {"Structured Spawn Data": 2.0, "PokemonDB Catch Rate": 1.0}

    results, _ = aggregator.aggregate_data(limit=1, weights=custom_weights)

    assert results[0].weighted_average == pytest.approx((4 * 2 + 8 * 1) / 3)


def test_infer_missing_rarity_for_absent_pokemon(monkeypatch):
    setup_common_mocks(monkeypatch, [("Missingmon", 999)])
    mock_infer = Mock(return_value=5.5)
    monkeypatch.setattr(aggregator, "infer_missing_rarity", mock_infer)

    results, _ = aggregator.aggregate_data(limit=1)

    mock_infer.assert_called_once_with("Missingmon", 999, "wild")
    assert results[0].average_score == pytest.approx(5.5)
    assert results[0].data_sources == []
    assert results[0].confidence == 0.0


@pytest.mark.parametrize(
    "score, expected",
    [
        (7.0, "Safe to Transfer"),
        (4.0, "Depends on Circumstances"),
    ],
)
def test_recommendations_at_thresholds(monkeypatch, score, expected):
    name = f"Mon{score}"
    setup_common_mocks(monkeypatch, [(name, 1)])
    structured_report = DataSourceReport(
        source_name="Structured Spawn Data", pokemon_count=1, success=True
    )
    monkeypatch.setattr(
        aggregator.structured_spawn,
        "scrape",
        lambda metrics=None: ({name: score}, structured_report),
    )

    results, _ = aggregator.aggregate_data(limit=1)

    assert results[0].weighted_average == pytest.approx(score)
    assert results[0].recommendation == expected
