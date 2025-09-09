"""Shared constants defining rarity score bands.

The module exposes global threshold values which can be tweaked at runtime.
This allows players to experiment with different rarity band definitions
without modifying the source code.  Call :func:`apply_thresholds` with a
mapping of ``common``/``uncommon``/``rare`` values to override the defaults.
"""

from typing import Dict, List, Tuple

# Default numeric thresholds for rarity bands. Higher scores mean more common
# Pokémon.  These can be overridden via :func:`apply_thresholds`.
COMMON: float = 7.0
UNCOMMON: float = 4.0
RARE: float = 2.0


def _build_score_bands() -> List[Tuple[float, str]]:
    """Construct the ordered list of score bands based on current globals."""

    return [
        (COMMON, "Common"),
        (UNCOMMON, "Uncommon"),
        (RARE, "Rare"),
        (float("-inf"), "Very Rare"),
    ]


# Ordered list of (minimum_score, band_name) pairs used for categorizing scores.
SCORE_BANDS: List[Tuple[float, str]] = _build_score_bands()


def apply_thresholds(values: Dict[str, float]) -> None:
    """Override the default rarity thresholds.

    Parameters
    ----------
    values:
        Mapping containing optional ``common``, ``uncommon`` and ``rare`` keys.
        Missing keys leave the corresponding defaults unchanged.
    """

    global COMMON, UNCOMMON, RARE, SCORE_BANDS
    if "common" in values:
        COMMON = float(values["common"])
    if "uncommon" in values:
        UNCOMMON = float(values["uncommon"])
    if "rare" in values:
        RARE = float(values["rare"])
    SCORE_BANDS = _build_score_bands()


def get_thresholds() -> Dict[str, float]:
    """Return the currently active rarity thresholds."""

    return {"common": COMMON, "uncommon": UNCOMMON, "rare": RARE}
