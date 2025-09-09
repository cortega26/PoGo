import logging
from typing import Dict, Optional, Tuple

import requests
from bs4 import BeautifulSoup
import re

from ..helpers import slugify_name, safe_request
from ..models import DataSourceReport

logger = logging.getLogger(__name__)


def parse_catch_rate(html: str) -> Optional[int]:
    """Extract the numeric catch rate from a PokemonDB page."""
    soup = BeautifulSoup(html, "html.parser")
    th = soup.find("th", string=lambda s: s and "Catch rate" in s)
    if not th:
        return None
    td = th.find_next("td")
    if not td:
        return None
    match = re.search(r"\d+", td.get_text())
    return int(match.group()) if match else None


def scrape_catch_rate(
    limit: Optional[int] = None,
    session: Optional[requests.Session] = None,
    metrics: Optional[Dict[str, float]] = None,
) -> Tuple[Dict[str, float], DataSourceReport]:
    """Scrape catch rates from PokemonDB and convert to rarity scores."""
    logger.info("Attempting to scrape Pokemon Database...")
    rarity_data: Dict[str, float] = {}
    sess = session or requests.Session()
    try:
        from ..aggregator import get_comprehensive_pokemon_list

        pokemon_list = get_comprehensive_pokemon_list()
        if limit is not None:
            pokemon_list = pokemon_list[:limit]
        for name, _ in pokemon_list:
            url = f"https://pokemondb.net/pokedex/{slugify_name(name)}"
            try:
                response = safe_request(url, session=sess, metrics=metrics)
                catch_rate = parse_catch_rate(response.text)
                if catch_rate is not None:
                    score = min(10.0, catch_rate / 25.5)
                    rarity_data[name] = score
            except Exception:
                continue
        report = DataSourceReport(
            source_name="PokemonDB Catch Rate",
            pokemon_count=len(rarity_data),
            success=True,
        )
    except Exception as e:
        logger.error("PokemonDB scraping failed: %s", e)
        report = DataSourceReport(
            source_name="PokemonDB Catch Rate",
            pokemon_count=0,
            success=False,
            error_message=str(e),
        )
    return rarity_data, report
