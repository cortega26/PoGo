from app import rarity_band
from pogorarity.thresholds import COMMON, UNCOMMON, RARE


def test_rarity_band_ordering():
    """Higher scores should correspond to more common bands."""
    assert rarity_band(RARE - 1) == "Very Rare"
    assert rarity_band((RARE + UNCOMMON) / 2) == "Rare"
    assert rarity_band((UNCOMMON + COMMON) / 2) == "Uncommon"
    assert rarity_band(COMMON + 1) == "Common"


def test_rarity_band_boundaries():
    """Boundary scores should fall into the correct bands."""
    assert rarity_band(RARE) == "Rare"
    assert rarity_band(UNCOMMON) == "Uncommon"
    assert rarity_band(COMMON) == "Common"
