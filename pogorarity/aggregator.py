import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .models import DataSourceReport, PokemonRarity
from .sources import (
    curated_spawn,
    pokemondb,
    structured_spawn,
    pokeapi,
    silph_road,
    game_master,
)
from .thresholds import COMMON, UNCOMMON

logger = logging.getLogger(__name__)

SOURCE_WEIGHTS = {
    "Structured Spawn Data": 1.0,
    "Enhanced Curated Data": 1.0,
    "PokemonDB Catch Rate": 2.0,
    "PokeAPI Capture Rate": 2.0,
    "Silph Road Spawn Tier": 0.5,
    "Game Master Spawn Weight": 1.0,
    "Game Master Capture Rate": 2.0,
}

RULES_PATH = Path(__file__).resolve().parent.parent / "data" / "infer_missing_rarity_rules.json"
try:
    RARITY_RULES = json.loads(RULES_PATH.read_text())
except Exception:
    RARITY_RULES = {}

SPAWN_TYPES_PATH = Path(__file__).resolve().parent.parent / "data" / "spawn_types.json"
_SPAWN_TYPES: Optional[Dict[str, str]] = None


def _load_weights(path: Path) -> Dict[str, float]:
    """Load source weights from a JSON file."""
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return {str(k): float(v) for k, v in data.items()}
    except Exception as exc:  # pragma: no cover - logging side effect
        logger.error("Failed to load weights from %s: %s", path, exc)
        return {}


def _load_spawn_types(path: Path) -> Dict[str, str]:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def get_comprehensive_pokemon_list() -> List[Tuple[str, int]]:
    """Get complete Pokemon list for all generations from data file."""
    data_path = Path(__file__).resolve().parent.parent / "data" / "pokemon_list.json"
    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)
    pokemon_list: List[Tuple[str, int]] = []
    for entry in data:
        name = entry.get("name")
        number = entry.get("number")
        if isinstance(name, str) and isinstance(number, int):
            pokemon_list.append((name, number))
    return pokemon_list


def categorize_pokemon_spawn_type(
    pokemon_name: str,
    pokemon_number: int,
    mapping_path: Optional[Path] = None,
) -> str:
    """Categorize Pokemon by spawn type using an external data file."""
    path = mapping_path or SPAWN_TYPES_PATH
    global _SPAWN_TYPES
    if _SPAWN_TYPES is None and path == SPAWN_TYPES_PATH:
        _SPAWN_TYPES = _load_spawn_types(path)
    mapping = _SPAWN_TYPES if path == SPAWN_TYPES_PATH else _load_spawn_types(path)
    return mapping.get(pokemon_name, "wild")


def get_trading_recommendation(score: float, spawn_type: str) -> str:
    """Return a trading recommendation based on rarity score and spawn type.

    Scores are on a 0--10 scale where higher numbers represent more common
    Pokémon.  The same numeric ranges are used by :func:`app.rarity_band` to
    display rarity bands.  Thresholds are defined in
    :mod:`pogorarity.thresholds`.

    Special spawn types take precedence over the numeric score.
    """

    if spawn_type == "legendary":
        return "Never Transfer (Legendary)"
    if spawn_type == "event-only":
        return "Never Transfer (Event Only)"
    if spawn_type == "evolution-only":
        return "Evaluate for Evolution"
    if score >= COMMON:
        return "Safe to Transfer"
    if score >= UNCOMMON:
        return "Depends on Circumstances"
    return "Keep or Trade Sparingly"


def infer_missing_rarity(pokemon_name: str, pokemon_number: int, spawn_type: str) -> float:
    if spawn_type in ["legendary", "event-only"]:
        return 0.0
    if spawn_type == "evolution-only":
        return 3.0
    rules = RARITY_RULES
    pseudo = rules.get("pseudo_legendaries", {})
    if pokemon_name in pseudo.get("pokemon", []):
        return pseudo.get("score", 0.0)
    starters = rules.get("starters", {})
    if pokemon_name in starters.get("pokemon", []):
        return starters.get("score", 0.0)
    very_common = rules.get("very_common", {})
    if pokemon_name in very_common.get("pokemon", []):
        return very_common.get("score", 0.0)
    regional_forms = rules.get("regional_forms", {})
    if any(region in pokemon_name for region in regional_forms.get("regions", [])):
        return regional_forms.get("score", 0.0)
    if pokemon_number <= 151:
        return 6.0
    if pokemon_number <= 251:
        return 5.5
    if pokemon_number <= 386:
        return 5.0
    if pokemon_number <= 493:
        return 4.5
    if pokemon_number <= 649:
        return 4.0
    return 3.5


def aggregate_data(
    limit: Optional[int] = None,
    metrics: Optional[Dict[str, float]] = None,
    weights: Optional[Dict[str, float]] = None,
    weights_path: Optional[Path] = None,
) -> Tuple[List[PokemonRarity], List[DataSourceReport]]:
    """Aggregate rarity data from all sources and compute recommendations."""
    pokemon_list = get_comprehensive_pokemon_list()
    limit = limit or len(pokemon_list)
    pokemon_list = pokemon_list[:limit]

    structured_data, structured_report = structured_spawn.scrape(metrics=metrics)
    curated_data, curated_report = curated_spawn.get_data()
    pokemondb_data, pokemondb_report = pokemondb.scrape_catch_rate(
        limit=limit, metrics=metrics
    )
    pokeapi_data, pokeapi_report = pokeapi.scrape_capture_rate(
        limit=limit, metrics=metrics
    )
    silph_data, silph_report = silph_road.scrape_spawn_tiers(metrics=metrics)
    gm_capture_data, gm_spawn_data, gm_reports = game_master.scrape(metrics=metrics)

    weight_map = weights
    if weight_map is None and weights_path:
        loaded = _load_weights(weights_path)
        if loaded:
            weight_map = loaded
    weight_map = weight_map or {}
    # Merge custom weights with defaults to ensure all sources are represented
    merged_weights = SOURCE_WEIGHTS.copy()
    merged_weights.update(weight_map)
    weight_map = merged_weights
    max_possible_weight = sum(weight_map.values())
    results: List[PokemonRarity] = []
    for pokemon_name, pokemon_number in pokemon_list:
        rarity_scores: Dict[str, float] = {}
        data_sources: List[str] = []
        spawn_type = categorize_pokemon_spawn_type(pokemon_name, pokemon_number)
        if pokemon_name in gm_spawn_data:
            rarity_scores["Game Master Spawn Weight"] = gm_spawn_data[pokemon_name]
            data_sources.append("Game Master Spawn Weight")
        else:
            if pokemon_name in structured_data:
                rarity_scores["Structured Spawn Data"] = structured_data[pokemon_name]
                data_sources.append("Structured Spawn Data")
            if pokemon_name in curated_data:
                rarity_scores["Enhanced Curated Data"] = curated_data[pokemon_name]
                data_sources.append("Enhanced Curated Data")
        if pokemon_name in silph_data:
            rarity_scores["Silph Road Spawn Tier"] = silph_data[pokemon_name]
            data_sources.append("Silph Road Spawn Tier")
        if pokemon_name in gm_capture_data:
            rarity_scores["Game Master Capture Rate"] = gm_capture_data[pokemon_name]
            data_sources.append("Game Master Capture Rate")
        else:
            if pokemon_name in pokemondb_data:
                rarity_scores["PokemonDB Catch Rate"] = pokemondb_data[pokemon_name]
                data_sources.append("PokemonDB Catch Rate")
            if pokemon_name in pokeapi_data:
                rarity_scores["PokeAPI Capture Rate"] = pokeapi_data[pokemon_name]
                data_sources.append("PokeAPI Capture Rate")
        if rarity_scores:
            total_weight = sum(weight_map.get(src, 1.0) for src in rarity_scores)
            weighted = sum(
                rarity_scores[src] * weight_map.get(src, 1.0) for src in rarity_scores
            )
            weighted_average = weighted / total_weight
            average_score = weighted_average
            confidence = (
                total_weight / max_possible_weight if max_possible_weight else 0.0
            )
            recommendation = get_trading_recommendation(average_score, spawn_type)
        else:
            average_score = infer_missing_rarity(
                pokemon_name, pokemon_number, spawn_type
            )
            weighted_average = average_score
            confidence = 0.0
            recommendation = get_trading_recommendation(average_score, spawn_type)
        results.append(
            PokemonRarity(
                name=pokemon_name,
                number=pokemon_number,
                rarity_scores=rarity_scores,
                average_score=average_score,
                weighted_average=weighted_average,
                confidence=confidence,
                recommendation=recommendation,
                data_sources=data_sources,
                spawn_type=spawn_type,
            )
        )
    reports = [
        structured_report,
        curated_report,
        pokemondb_report,
        pokeapi_report,
        silph_report,
        *gm_reports,
    ]
    return results, reports
