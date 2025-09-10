from pathlib import Path
import json
from typing import List, Optional

import pandas as pd
import streamlit as st

from pogorarity.health import check_cache
from pogorarity import aggregator, thresholds
from pogorarity.config import load_config, apply_config

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

SOURCE_COLS = {
    "Structured Spawn Data": "Structured_Spawn_Data_Score",
    "Enhanced Curated Data": "Enhanced_Curated_Data_Score",
    "PokemonDB Catch Rate": "PokemonDB_Catch_Rate_Score",
}


def generation_from_number(num: int) -> int:
    for start, end, gen in GENERATION_RANGES:
        if start <= num <= end:
            return gen
    return 0


def rarity_band(score: float) -> str:
    """Map a numeric rarity score to a human-friendly rarity band.

    Higher scores indicate more common Pokémon.  The score bands and
    thresholds shared with
    :func:`pogorarity.aggregator.get_trading_recommendation` are defined in
    :mod:`pogorarity.thresholds`.

    Parameters
    ----------
    score:
        A floating point rarity score from 0 (rarest) to 10 (most
        common).

    Returns
    -------
    str
        One of "Very Rare", "Rare", "Uncommon", or "Common".
    """

    for threshold, label in thresholds.SCORE_BANDS:
        if score >= threshold:
            return label
    # Fallback, though SCORE_BANDS should cover all scores
    return thresholds.SCORE_BANDS[-1][1]


@st.cache_data
def load_data(_thresholds_sig: Optional[tuple] = None) -> pd.DataFrame:
    """Load rarity data and augment with generation and rarity band.

    The cached result incorporates the active thresholds to ensure the
    ``Rarity_Band`` column reflects any configuration overrides.
    """

    base_cols = [
        "Number",
        "Name",
        "Spawn_Type",
        "Average_Rarity_Score",
        "Recommendation",
        "Data_Sources",
        "Structured_Spawn_Data_Score",
        "Enhanced_Curated_Data_Score",
        "PokemonDB_Catch_Rate_Score",
    ]
    optional_cols = [
        "Weighted_Average_Rarity_Score",
        "Confidence",
    ]

    header = pd.read_csv(
        DATA_FILE,
        sep=";",
        decimal=",",
        nrows=0,
        encoding="utf-8",
    ).columns
    usecols = [c for c in base_cols if c in header]
    usecols.extend(c for c in optional_cols if c in header)

    df = pd.read_csv(
        DATA_FILE,
        sep=";",
        decimal=",",
        usecols=usecols,
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

    config = load_config()
    apply_config(config)

    run_info = load_run_log()
    health_info = check_cache()
    thresholds_sig = tuple(thresholds.get_thresholds().values())
    df = load_data(thresholds_sig)

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
    if "Weighted_Average_Rarity_Score" in result.columns:
        display_cols.append("Weighted_Average_Rarity_Score")
    if "Confidence" in result.columns:
        display_cols.append("Confidence")
    st.dataframe(result[display_cols], use_container_width=True)

    selected_name = st.selectbox(
        "Select a Pokémon for details",
        result["Name"].unique(),
    )
    if st.button("Show Details"):
        row = result[result["Name"] == selected_name].iloc[0]
        sources = str(row.get("Data_Sources", "") or "").strip()
        if not sources:
            st.info(
                "No direct data available; rarity score inferred from heuristics."
            )
        else:
            st.write("Sources:", sources)
        spawn_type = row.get("Spawn_Type", "wild")
        st.write("Spawn Type:", spawn_type)

        weighted_avg = row.get("Weighted_Average_Rarity_Score")
        if weighted_avg is not None and not pd.isna(weighted_avg):
            st.write("Weighted Average:", weighted_avg)
        st.write("Average Score:", row["Average_Rarity_Score"])

        confidence = row.get("Confidence")
        if confidence is not None and not pd.isna(confidence):
            st.write("Confidence:", confidence)

        thresh = thresholds.get_thresholds()
        st.caption(
            "Score thresholds – Common ≥ {common}, Uncommon ≥ {uncommon}, "
            "Rare ≥ {rare}".format(**thresh)
        )
        if spawn_type in {"legendary", "event-only", "evolution-only"}:
            st.warning(
                "Spawn type override applied; recommendation may ignore thresholds."
            )

        contrib_rows = []
        total_weight = 0.0
        for source, col in SOURCE_COLS.items():
            score = row.get(col)
            if score is not None and not pd.isna(score):
                weight = aggregator.SOURCE_WEIGHTS.get(source, 1.0)
                contrib_rows.append({"Source": source, "Score": score, "Weight": weight})
                total_weight += weight
        if contrib_rows:
            contrib_df = pd.DataFrame(contrib_rows)
            if total_weight:
                contrib_df["Contribution"] = (
                    contrib_df["Score"] * contrib_df["Weight"]
                ) / total_weight
            st.table(contrib_df)
        st.caption(f"Spawn types file: {aggregator.SPAWN_TYPES_PATH}")


if __name__ == "__main__":
    main()
