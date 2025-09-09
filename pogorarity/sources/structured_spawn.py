import logging
from typing import Dict, Optional, Tuple

from ..helpers import safe_request
from ..models import DataSourceReport

logger = logging.getLogger(__name__)


def scrape(metrics: Optional[Dict[str, float]] = None) -> Tuple[Dict[str, float], DataSourceReport]:
    """Fetch spawn rates from a public JSON dataset."""
    logger.info("Fetching structured spawn data...")
    rarity_data: Dict[str, float] = {}
    url = "https://raw.githubusercontent.com/Biuni/PokemonGO-Pokedex/master/pokedex.json"
    try:
        response = safe_request(url, metrics=metrics)
        data = response.json()
        for entry in data.get("pokemon", []):
            name = entry.get("name")
            spawn_chance = entry.get("spawn_chance")
            if name and spawn_chance is not None:
                try:
                    chance = float(spawn_chance)
                    score = min(10.0, max(0.0, chance / 2.0))
                    rarity_data[name] = score
                except (TypeError, ValueError):
                    continue
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
    return rarity_data, report
