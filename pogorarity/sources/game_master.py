import logging
from typing import Dict, List, Optional, Tuple

from ..helpers import safe_request
from ..models import DataSourceReport

logger = logging.getLogger(__name__)

GAME_MASTER_URL = "https://raw.githubusercontent.com/PokeMiners/game_masters/master/latest/latest.json"


def _format_name(pokemon_id: str) -> str:
    """Convert a GAME_MASTER pokemonId to a canonical display name."""
    name = pokemon_id.replace("_FEMALE", "♀").replace("_MALE", "♂")
    return name.replace("_", " ").title()


def scrape(
    metrics: Optional[Dict[str, float]] = None,
    *,
    capture_expected_min: float = 0.0,
    capture_expected_max: float = 1.0,
    spawn_expected_min: float = 0.0,
    spawn_expected_max: Optional[float] = None,
    auto_scale_spawn: bool = False,
    on_out_of_range: str = "clamp",
) -> Tuple[Dict[str, float], Dict[str, float], List[DataSourceReport]]:
    """Parse Game Master data for capture rates and spawn weights.

    Returns two dictionaries mapping Pokémon names to 0--10 rarity scores:
    one for ``base_capture_rate`` and one for ``spawnWeight``.  Missing values
    are ignored.  ``spawn_expected_max`` defaults to the maximum observed weight
    when not provided.
    """

    from ..scaling import scale_records

    logger.info("Fetching Game Master data...")
    capture_records: List[Tuple[str, float]] = []
    spawn_records: List[Tuple[str, float]] = []
    try:
        response = safe_request(GAME_MASTER_URL, metrics=metrics)
        data = response.json()
        for entry in data:
            data_obj = entry.get("data", {})
            pokemon_settings = data_obj.get("pokemonSettings")
            if not pokemon_settings:
                continue
            pokemon_id = pokemon_settings.get("pokemonId")
            if not isinstance(pokemon_id, str):
                continue
            name = _format_name(pokemon_id)
            encounter = pokemon_settings.get("encounter", {})
            base_capture = (
                encounter.get("base_capture_rate")
                or encounter.get("baseCaptureRate")
                or pokemon_settings.get("base_capture_rate")
                or pokemon_settings.get("baseCaptureRate")
            )
            if isinstance(base_capture, (int, float)):
                capture_records.append((name, float(base_capture)))
            spawn_weight = (
                pokemon_settings.get("spawnWeight")
                or pokemon_settings.get("spawn_weight")
                or encounter.get("spawnWeight")
                or encounter.get("spawn_weight")
            )
            if isinstance(spawn_weight, (int, float)):
                spawn_records.append((name, float(spawn_weight)))
        capture_rates = scale_records(
            capture_records,
            capture_expected_min,
            capture_expected_max,
            False,
            on_out_of_range=on_out_of_range,
        )
        spawn_max = (
            spawn_expected_max
            if spawn_expected_max is not None
            else max((v for _, v in spawn_records), default=0.0)
        )
        spawn_weights = scale_records(
            spawn_records,
            spawn_expected_min,
            spawn_max,
            auto_scale_spawn,
            on_out_of_range=on_out_of_range,
        )
        capture_report = DataSourceReport(
            source_name="Game Master Capture Rate",
            pokemon_count=len(capture_rates),
            success=len(capture_rates) > 0,
        )
        if len(capture_rates) == 0:
            capture_report.error_message = "No data found"
        spawn_report = DataSourceReport(
            source_name="Game Master Spawn Weight",
            pokemon_count=len(spawn_weights),
            success=len(spawn_weights) > 0,
        )
        if len(spawn_weights) == 0:
            spawn_report.error_message = "No data found"
        return capture_rates, spawn_weights, [capture_report, spawn_report]
    except Exception as e:
        logger.error("Game Master fetch failed: %s", e)
        capture_report = DataSourceReport(
            source_name="Game Master Capture Rate",
            pokemon_count=0,
            success=False,
            error_message=str(e),
        )
        spawn_report = DataSourceReport(
            source_name="Game Master Spawn Weight",
            pokemon_count=0,
            success=False,
            error_message=str(e),
        )
        return {}, {}, [capture_report, spawn_report]
