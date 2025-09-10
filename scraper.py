import logging
from typing import Dict, Iterable, Tuple, List

from pogorarity.scaling import scale_records

logger = logging.getLogger(__name__)


def scrape_structured_spawn_data(
    entries: Iterable[Dict[str, float]],
    *,
    expected_min: float = 0.0,
    expected_max: float = 20.0,
    auto_scale: bool = False,
    on_out_of_range: str = "clamp",
) -> Dict[str, float]:
    """Compute scores from structured spawn data entries."""
    records = []
    for entry in entries:
        name = entry.get("name")
        spawn_chance = entry.get("spawn_chance")
        if name is None or spawn_chance is None:
            continue
        try:
            records.append((name, float(spawn_chance)))
        except (TypeError, ValueError):
            continue
    return scale_records(
        records, expected_min, expected_max, auto_scale, on_out_of_range=on_out_of_range
    )


def scrape_pokemondb_catch_rate(
    catch_rates: Dict[str, float],
    *,
    expected_min: float = 0.0,
    expected_max: float = 255.0,
    auto_scale: bool = False,
    on_out_of_range: str = "clamp",
) -> Dict[str, float]:
    """Compute scores from PokemonDB catch rate data."""
    records = []
    for name, rate in catch_rates.items():
        try:
            records.append((name, float(rate)))
        except (TypeError, ValueError):
            continue
    return scale_records(
        records, expected_min, expected_max, auto_scale, on_out_of_range=on_out_of_range
    )
