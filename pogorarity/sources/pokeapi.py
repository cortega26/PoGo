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
) -> Tuple[Dict[str, float], DataSourceReport]:
    """Fetch capture rates from PokeAPI and normalize to 0-10 scale."""
    logger.info("Attempting to scrape PokeAPI...")
    rarity_data: Dict[str, float] = {}
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
                    score = min(10.0, capture_rate / 25.5)
                    rarity_data[name] = score
            except Exception:
                continue
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
    return rarity_data, report
