import logging
from typing import Dict, Optional, Tuple

from ..helpers import safe_request
from ..models import DataSourceReport

logger = logging.getLogger(__name__)


def scrape(
    metrics: Optional[Dict[str, float]] = None,
    *,
    expected_min: float = 0.0,
    expected_max: float = 20.0,
    auto_scale: bool = False,
    on_out_of_range: str = "clamp",
) -> Tuple[Dict[str, float], DataSourceReport]:
    """Fetch spawn rates from a public JSON dataset."""
    from ..scaling import scale_records

    logger.info("Fetching structured spawn data...")
    records = []
    url = "https://raw.githubusercontent.com/Biuni/PokemonGO-Pokedex/master/pokedex.json"
    try:
        response = safe_request(url, metrics=metrics)
        data = response.json()
        for entry in data.get("pokemon", []):
            name = entry.get("name")
            spawn_chance = entry.get("spawn_chance")
            if name and spawn_chance is not None:
                try:
                    records.append((name, float(spawn_chance)))
                except (TypeError, ValueError):
                    continue
        rarity_data = scale_records(
            records,
            expected_min,
            expected_max,
            auto_scale,
            on_out_of_range=on_out_of_range,
        )
        report = DataSourceReport(
            source_name="Structured Spawn Data",
            pokemon_count=len(rarity_data),
            success=len(rarity_data) > 0,
        )
        if len(rarity_data) == 0:
            report.error_message = "No data found"
    except Exception as e:
        logger.error("Structured spawn data fetch failed: %s", e)
        report = DataSourceReport(
            source_name="Structured Spawn Data",
            pokemon_count=0,
            success=False,
            error_message=str(e),
        )
        rarity_data = {}
    return rarity_data, report
