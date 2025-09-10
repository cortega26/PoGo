import logging
from typing import Dict, Iterable, Tuple

logger = logging.getLogger(__name__)


def scale_records(
    records: Iterable[Tuple[str, float]],
    expected_min: float,
    expected_max: float,
    auto_scale: bool,
    *,
    on_out_of_range: str = "clamp",
) -> Dict[str, float]:
    """Scale raw numeric values to a 0--10 range.

    Args:
        records: Iterable of ``(name, value)`` pairs.
        expected_min: Minimum expected raw value.
        expected_max: Maximum expected raw value.
        auto_scale: Whether to expand the range to include observed
            out-of-range values.
        on_out_of_range: If ``"discard"``, drop values outside the expected
            range when ``auto_scale`` is ``False``.  Otherwise clamp to the
            nearest boundary.
    """
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
