import json
import logging
from pathlib import Path
from typing import Dict, Tuple

from ..models import DataSourceReport

logger = logging.getLogger(__name__)


def get_data() -> Tuple[Dict[str, float], DataSourceReport]:
    """Load curated spawn data from a bundled JSON file."""
    logger.info("Loading enhanced curated spawn data...")
    data_path = Path(__file__).parent.parent / "data" / "curated_spawn_data.json"
    try:
        with open(data_path, encoding="utf-8") as f:
            spawn_data = json.load(f)
        report = DataSourceReport(
            source_name="Enhanced Curated Data",
            pokemon_count=len(spawn_data),
            success=True,
        )
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error("Curated spawn data load failed: %s", e)
        spawn_data = {}
        report = DataSourceReport(
            source_name="Enhanced Curated Data",
            pokemon_count=0,
            success=False,
            error_message=str(e),
        )
    return spawn_data, report
