import sys
from pathlib import Path
import json
from typing import List, Optional

import pandas as pd
import streamlit as st

from pogorarity.health import check_cache

DATA_FILE = Path(__file__).with_name("pokemon_rarity_analysis_enhanced.csv")
RUN_LOG_FILE = Path(__file__).resolve().parent / "pogorarity" / "run_log.jsonl"

GENERATION_RANGES = [
    (1, 151, 1),
    (152, 251, 2),
    (252, 386, 3),
    (387, 493, 4),
    (494, 649, 5),
    (650, 721, 6),
    (722, 809, 7),
    (810, 905, 8),
    (906, 1010, 9),
]


def generation_from_number(num: int) -> int:
    for start, end, gen in GENERATION_RANGES:
        if start <= num <= end:
            return gen
    return 0


def rarity_band(score: float) -> str:
    if score < 1:
        return "Common"
    if score < 2:
        return "Uncommon"
    if score < 3:
        return "Rare"
    return "Very Rare"


@st.cache_data
def load_data() -> pd.DataFrame:
    cols = [
        "Number",
        "Name",
        "Spawn_Type",
        "Average_Rarity_Score",
        "Recommendation",
        "Data_Sources",
        "Structured_Spawn_Data_Score",
        "Enhanced_Curated_Data_Score",
        "PokemonDB_Catch_Rate_Score",
        "Inferred_Score",
    ]
    df = pd.read_csv(
        DATA_FILE,
        sep=";",
        decimal=",",
        usecols=cols,
        encoding="utf-8",
    )
    df["Generation"] = df["Number"].apply(generation_from_number)
    df["Rarity_Band"] = df["Average_Rarity_Score"].apply(rarity_band)
    return df


@st.cache_data
def load_run_log() -> dict:
    if RUN_LOG_FILE.exists():
        lines = RUN_LOG_FILE.read_text(encoding="utf-8").strip().splitlines()
        if lines:
            return json.loads(lines[-1])
    return {}


def apply_filters(
    df: pd.DataFrame,
    species: Optional[List[str]] = None,
    generation: Optional[int] = None,
    rarity: Optional[str] = None,
    search: Optional[str] = None,
) -> pd.DataFrame:
    result = df
    if species:
        result = result[result["Name"].isin(species)]
    if generation:
        result = result[result["Generation"] == generation]
    if rarity:
        result = result[result["Rarity_Band"] == rarity]
    if search:
        result = result[result["Name"].str.contains(search, case=False)]
    return result


def main() -> None:
    st.markdown(
        "<h1 style='text-align: center; color: white;'>Pokémon Rarity Recommendations</h1>",
        unsafe_allow_html=True,
    )

    run_info = load_run_log()
    health_info = check_cache()
    df = load_data()

    st.sidebar.header("Status")
    if run_info:
        st.sidebar.write(f"Run ID: {run_info.get('run_id')}")
        st.sidebar.write(f"Status: {run_info.get('status')}")
        if run_info.get("rows") is not None:
            st.sidebar.write(f"Rows: {run_info['rows']}")
        if run_info.get("error"):
            st.sidebar.error(run_info["error"])
    else:
        st.sidebar.write("No runs logged.")
    st.sidebar.write(f"Cache fresh: {health_info['cache_fresh']}")
    st.sidebar.write(f"Last updated: {health_info['last_updated']}")

    st.sidebar.header("Filters")
    species = st.sidebar.multiselect("Species", sorted(df["Name"].unique()))
    generation = st.sidebar.selectbox(
        "Generation", ["All"] + sorted(df["Generation"].unique())
    )
    rarity = st.sidebar.selectbox(
        "Rarity Band", ["All"] + sorted(df["Rarity_Band"].unique())
    )
    search = st.sidebar.text_input("Search")

    gen_val = generation if generation != "All" else None
    rarity_val = rarity if rarity != "All" else None
    result = apply_filters(df, species or None, gen_val, rarity_val, search or None)

    if result.empty:
        st.warning("No Pokémon match the filters.")
        return

    display_cols = [
        "Name",
        "Generation",
        "Rarity_Band",
        "Recommendation",
        "Average_Rarity_Score",
    ]
    st.dataframe(result[display_cols])

    for _, row in result.iterrows():
        with st.expander(f"Why {row['Name']}?"):
            st.write("Sources:", row["Data_Sources"])
            st.write("Confidence:", row["Average_Rarity_Score"])
            st.write(
                {
                    "Structured": row["Structured_Spawn_Data_Score"],
                    "Curated": row["Enhanced_Curated_Data_Score"],
                    "Catch Rate": row["PokemonDB_Catch_Rate_Score"],
                    "Inferred": row["Inferred_Score"],
                }
            )


if __name__ == "__main__":
    main()
