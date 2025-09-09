"""pogorarity package."""

from .scraper import EnhancedRarityScraper
from .models import PokemonRarity, DataSourceReport, RarityRecord
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
    "EnhancedRarityScraper",
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
