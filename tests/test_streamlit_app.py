import pandas as pd

from app import load_data, apply_filters

def test_load_data_has_gen_and_rarity():
    df = load_data()
    assert "Generation" in df.columns
    assert "Rarity_Band" in df.columns
    assert not df.empty

def test_apply_filters_generation_and_rarity():
    df = pd.DataFrame(
        {
            "Name": ["Bulbasaur", "Chikorita"],
            "Generation": [1, 2],
            "Rarity_Band": ["Rare", "Common"],
        }
    )
    filtered = apply_filters(df, generation=1)
    assert list(filtered["Name"]) == ["Bulbasaur"]
    filtered = apply_filters(df, rarity="Common")
    assert list(filtered["Name"]) == ["Chikorita"]
