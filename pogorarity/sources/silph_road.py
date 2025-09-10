import logging
from typing import Dict, Optional, Tuple

import requests

from ..helpers import safe_request
from ..models import DataSourceReport

logger = logging.getLogger(__name__)

# Public dataset of community reported spawn tiers
SILPH_ROAD_TIER_URL = (
    "https://raw.githubusercontent.com/TheSilphRoad/pogodata/master/spawn-tiers.json"
)


def scrape_spawn_tiers(
    session: Optional[requests.Session] = None,
    metrics: Optional[Dict[str, float]] = None,
    *,
    expected_min: float = 1.0,
    expected_max: float = 5.0,
    auto_scale: bool = False,
    on_out_of_range: str = "clamp",
) -> Tuple[Dict[str, float], DataSourceReport]:
    """Fetch Silph Road spawn tiers and convert to rarity scores."""
    from ..scaling import scale_records

    logger.info("Fetching Silph Road spawn tier data...")
    records = []
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
            if name and isinstance(tier, (int, float)):
                records.append((name, float(tier)))
        scaled = scale_records(
            records,
            expected_min,
            expected_max,
            auto_scale,
            on_out_of_range=on_out_of_range,
        )
        rarity_data = {name: 10.0 - score for name, score in scaled.items()}
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
        rarity_data = {}
    return rarity_data, report
