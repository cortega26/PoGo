"""Shared constants defining rarity score bands."""

from typing import List, Tuple

# Numeric thresholds for rarity bands. Higher scores mean more common Pokémon.
COMMON = 7.0
UNCOMMON = 4.0
RARE = 2.0

# Ordered list of (minimum_score, band_name) pairs used for categorizing scores.
SCORE_BANDS: List[Tuple[float, str]] = [
    (COMMON, "Common"),
    (UNCOMMON, "Uncommon"),
    (RARE, "Rare"),
    (float("-inf"), "Very Rare"),
]
