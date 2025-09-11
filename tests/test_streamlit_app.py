import pandas as pd

from app import load_data, apply_filters

def test_load_data_has_gen_and_rarity():
    df = load_data()
    assert "Generation" in df.columns
    assert "Rarity_Band" in df.columns
    assert "Type" in df.columns
    assert "Region" in df.columns
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


def test_apply_filters_caught_status():
    df = pd.DataFrame(
        {
            "Name": ["Bulbasaur", "Chikorita"],
            "Generation": [1, 2],
            "Rarity_Band": ["Rare", "Common"],
        }
    )
    caught = {"Bulbasaur"}
    filtered = apply_filters(df, caught_set=caught, caught=True)
    assert list(filtered["Name"]) == ["Bulbasaur"]
    filtered = apply_filters(df, caught_set=caught, caught=False)
    assert list(filtered["Name"]) == ["Chikorita"]


def test_apply_filters_type_and_region():
    df = pd.DataFrame(
        {
            "Name": ["Bulbasaur", "Chikorita"],
            "Generation": [1, 2],
            "Rarity_Band": ["Rare", "Common"],
            "Type": ["grass, poison", "grass"],
            "Region": ["kanto", "johto"],
        }
    )
    filtered = apply_filters(df, types=["poison"])
    assert list(filtered["Name"]) == ["Bulbasaur"]
    filtered = apply_filters(df, regions=["johto"])
    assert list(filtered["Name"]) == ["Chikorita"]
