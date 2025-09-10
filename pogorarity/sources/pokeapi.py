import logging
from typing import Dict, Optional, Tuple

import requests

from ..helpers import safe_request
from ..models import DataSourceReport

logger = logging.getLogger(__name__)


def scrape_capture_rate(
    limit: Optional[int] = None,
    session: Optional[requests.Session] = None,
    metrics: Optional[Dict[str, float]] = None,
    *,
    expected_min: float = 0.0,
    expected_max: float = 255.0,
    auto_scale: bool = False,
    on_out_of_range: str = "clamp",
) -> Tuple[Dict[str, float], DataSourceReport]:
    """Fetch capture rates from PokeAPI and normalize to 0-10 scale."""
    from ..scaling import scale_records

    logger.info("Attempting to scrape PokeAPI...")
    records = []
    sess = session or requests.Session()
    try:
        from ..aggregator import get_comprehensive_pokemon_list

        pokemon_list = get_comprehensive_pokemon_list()
        if limit is not None:
            pokemon_list = pokemon_list[:limit]
        for name, number in pokemon_list:
            url = f"https://pokeapi.co/api/v2/pokemon-species/{number}"
            try:
                response = safe_request(url, session=sess, metrics=metrics)
                data = response.json()
                capture_rate = data.get("capture_rate")
                if isinstance(capture_rate, (int, float)):
                    records.append((name, float(capture_rate)))
            except Exception:
                continue
        rarity_data = scale_records(
            records,
            expected_min,
            expected_max,
            auto_scale,
            on_out_of_range=on_out_of_range,
        )
        report = DataSourceReport(
            source_name="PokeAPI Capture Rate",
            pokemon_count=len(rarity_data),
            success=True,
        )
    except Exception as e:
        logger.error("PokeAPI scraping failed: %s", e)
        report = DataSourceReport(
            source_name="PokeAPI Capture Rate",
            pokemon_count=0,
            success=False,
            error_message=str(e),
        )
        rarity_data = {}
    return rarity_data, report
