import logging
from typing import Dict, Optional, Tuple

import requests

from ..helpers import safe_request
from ..models import DataSourceReport

logger = logging.getLogger(__name__)

# Mapping from Silph Road spawn tiers to 0–10 rarity scores
SILPH_ROAD_TIER_MAPPING: Dict[int, float] = {
    1: 9.0,  # very common spawns
    2: 7.0,
    3: 5.0,
    4: 3.0,
    5: 1.0,  # extremely rare spawns
}

# Public dataset of community reported spawn tiers
SILPH_ROAD_TIER_URL = (
    "https://raw.githubusercontent.com/TheSilphRoad/pogodata/master/spawn-tiers.json"
)


def scrape_spawn_tiers(
    session: Optional[requests.Session] = None,
    metrics: Optional[Dict[str, float]] = None,
) -> Tuple[Dict[str, float], DataSourceReport]:
    """Fetch Silph Road spawn tiers and convert to rarity scores."""
    logger.info("Fetching Silph Road spawn tier data...")
    rarity_data: Dict[str, float] = {}
    sess = session or requests.Session()
    try:
        response = safe_request(SILPH_ROAD_TIER_URL, session=sess, metrics=metrics)
        data = response.json()
        # Data may be a list of entries or mapping name->tier
        if isinstance(data, dict):
            entries = [
                {"name": name, "tier": tier}
                for name, tier in data.items()
            ]
        elif isinstance(data, list):
            entries = data
        else:
            entries = []
        for entry in entries:
            name = entry.get("name") or entry.get("pokemon")
            tier = entry.get("tier") or entry.get("spawn_tier") or entry.get("spawnTier")
            if isinstance(tier, str):
                try:
                    tier = int(tier)
                except ValueError:
                    continue
            if name and isinstance(tier, int) and tier in SILPH_ROAD_TIER_MAPPING:
                rarity_data[name] = SILPH_ROAD_TIER_MAPPING[tier]
        report = DataSourceReport(
            source_name="Silph Road Spawn Tier",
            pokemon_count=len(rarity_data),
            success=len(rarity_data) > 0,
        )
        if len(rarity_data) == 0:
            report.error_message = "No data found"
    except Exception as e:
        logger.error("Silph Road spawn tier fetch failed: %s", e)
        report = DataSourceReport(
            source_name="Silph Road Spawn Tier",
            pokemon_count=0,
            success=False,
            error_message=str(e),
        )
    return rarity_data, report
