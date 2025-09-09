from app import rarity_band


def test_rarity_band_ordering():
    """Higher scores should correspond to more common bands."""
    assert rarity_band(1.0) == "Very Rare"
    assert rarity_band(3.0) == "Rare"
    assert rarity_band(5.0) == "Uncommon"
    assert rarity_band(8.0) == "Common"


def test_rarity_band_boundaries():
    """Boundary scores should fall into the correct bands."""
    assert rarity_band(2.0) == "Rare"
    assert rarity_band(4.0) == "Uncommon"
    assert rarity_band(7.0) == "Common"
