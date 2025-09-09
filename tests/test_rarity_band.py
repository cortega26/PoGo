from app import rarity_band


def test_rarity_band_ordering():
    """Higher scores should correspond to more common bands."""
    assert rarity_band(0.5) == "Very Rare"
    assert rarity_band(1.5) == "Rare"
    assert rarity_band(2.5) == "Uncommon"
    assert rarity_band(5.0) == "Common"
