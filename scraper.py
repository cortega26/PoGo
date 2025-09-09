import logging
from typing import Dict, Iterable, Tuple, List

logger = logging.getLogger(__name__)


def _scale_records(
    records: Iterable[Tuple[str, float]],
    expected_min: float,
    expected_max: float,
    auto_scale: bool,
    *,
    on_out_of_range: str = "clamp",
) -> Dict[str, float]:
    records = list(records)
    if not records:
        return {}
    values = [v for _, v in records]
    observed_min = min(values)
    observed_max = max(values)
    range_min, range_max = expected_min, expected_max
    if observed_min < expected_min or observed_max > expected_max:
        logger.warning(
            "Observed values outside expected range [%s, %s]; min=%s max=%s",
            expected_min,
            expected_max,
            observed_min,
            observed_max,
        )
        if auto_scale:
            range_min = min(observed_min, range_min)
            range_max = max(observed_max, range_max)
    if range_max == range_min:
        return {name: 0.0 for name, _ in records}
    scaled: Dict[str, float] = {}
    for name, value in records:
        if not auto_scale and (value < expected_min or value > expected_max):
            if on_out_of_range == "discard":
                logger.warning(
                    "Discarding %s value %s outside expected range", name, value
                )
                continue
        score = 10.0 * (value - range_min) / (range_max - range_min)
        score = max(0.0, min(10.0, score))
        scaled[name] = score
    return scaled


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
    return _scale_records(
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
    return _scale_records(
        records, expected_min, expected_max, auto_scale, on_out_of_range=on_out_of_range
    )
