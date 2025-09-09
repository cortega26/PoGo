"""pogorarity package."""

from .aggregator import (
    aggregate_data,
    categorize_pokemon_spawn_type,
    get_comprehensive_pokemon_list,
    get_trading_recommendation,
    infer_missing_rarity,
)
from .helpers import safe_request, slugify_name
from .models import DataSourceReport, PokemonRarity, RarityRecord
from .adapters import (
    get_go_hub_records,
    get_pokemondb_records,
    get_structured_spawn_records,
    parse_go_hub,
    parse_pokemondb_page,
    parse_structured_spawn_data,
)
from .normalizer import Encounter, Rarity, normalize_encounters

__all__ = [
    "aggregate_data",
    "categorize_pokemon_spawn_type",
    "get_comprehensive_pokemon_list",
    "get_trading_recommendation",
    "infer_missing_rarity",
    "safe_request",
    "slugify_name",
    "PokemonRarity",
    "DataSourceReport",
    "RarityRecord",
    "get_go_hub_records",
    "get_pokemondb_records",
    "get_structured_spawn_records",
    "parse_go_hub",
    "parse_pokemondb_page",
    "parse_structured_spawn_data",
    "Encounter",
    "Rarity",
    "normalize_encounters",
]
