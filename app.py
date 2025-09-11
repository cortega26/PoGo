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
CAUGHT_FILE = Path(__file__).with_name("caught_pokemon.json")

DEFAULT_GENERATION_RANGES = [
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

CONFIG = load_config()
GENERATION_RANGES = CONFIG.get("generation_ranges", DEFAULT_GENERATION_RANGES)
st.set_page_config(page_title="Pokémon Rarity", layout="wide")

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


def load_caught() -> set[str]:
    """Return the set of Pokémon marked as caught."""
    if CAUGHT_FILE.exists():
        try:
            return set(json.loads(CAUGHT_FILE.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            return set()
    return set()


def save_caught(caught: set[str]) -> None:
    """Persist the caught Pokémon set to disk."""
    CAUGHT_FILE.write_text(
        json.dumps(sorted(caught)), encoding="utf-8"
    )


def apply_filters(
    df: pd.DataFrame,
    species: Optional[List[str]] = None,
    generation: Optional[int] = None,
    rarity: Optional[str] = None,
    search: Optional[str] = None,
    caught_set: Optional[set[str]] = None,
    caught: Optional[bool] = None,
) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)
    if species:
        mask &= df["Name"].isin(species)
    if generation:
        mask &= df["Generation"] == generation
    if rarity:
        mask &= df["Rarity_Band"] == rarity
    if search:
        mask &= df["Name"].str.contains(search, case=False)
    if caught is not None and caught_set is not None:
        if caught:
            mask &= df["Name"].isin(caught_set)
        else:
            mask &= ~df["Name"].isin(caught_set)
    return df[mask]


def main() -> None:
    st.title("Pokémon Rarity Recommendations")
    st.divider()

    apply_config(CONFIG)

    run_info = load_run_log()
    health_info = check_cache()
    thresholds_sig = tuple(thresholds.get_thresholds().values())
    df = load_data(thresholds_sig)
    caught_set = st.session_state.setdefault("caught_set", load_caught())

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


    with st.sidebar.expander("Filters", expanded=True):
        reset = st.button("Reset filters")
        if reset:
            st.session_state.species = []
            st.session_state.generation = "All"
            st.session_state.rarity = "All"
            st.session_state.search = ""
            st.session_state.caught_filter = "All"
        with st.form("filters"):
            species = st.multiselect(
                "Species",
                sorted(df["Name"].unique()),
                key="species",
                help="Limit results to selected Pokémon",
            )
            generation = st.selectbox(
                "Generation",
                ["All"] + sorted(df["Generation"].unique()),
                key="generation",
                help="Filter by Pokémon generation",
            )
            rarity = st.selectbox(
                "Rarity Band",
                ["All"] + sorted(df["Rarity_Band"].unique()),
                key="rarity",
                help="Filter by rarity band",
            )
            search = st.text_input(
                "Search",
                key="search",
                help="Search by Pokémon name",
            )
            caught_option = st.selectbox(
                "Caught Status",
                ["All", "Caught", "Uncaught"],
                key="caught_filter",
                help="Filter by caught status",
            )
            st.form_submit_button("Apply")

    if reset:
        result = df
    else:
        gen_val = st.session_state.get("generation", "All")
        rarity_val = st.session_state.get("rarity", "All")
        gen_val = gen_val if gen_val != "All" else None
        rarity_val = rarity_val if rarity_val != "All" else None
        caught_val = st.session_state.get("caught_filter", "All")
        caught_bool = None if caught_val == "All" else (caught_val == "Caught")
        result = apply_filters(
            df,
            st.session_state.get("species") or None,
            gen_val,
            rarity_val,
            st.session_state.get("search") or None,
            caught_set,
            caught_bool,
        )

    if result.empty:
        st.warning("No Pokémon match the filters.")
        return

    result = result.copy()
    result["Caught"] = result["Name"].isin(caught_set)
    display_cols = [
        "Name",
        "Generation",
        "Rarity_Band",
        "Recommendation",
        "Average_Rarity_Score",
        "Caught",
    ]
    if "Weighted_Average_Rarity_Score" in result.columns:
        display_cols.append("Weighted_Average_Rarity_Score")
    if "Confidence" in result.columns:
        display_cols.append("Confidence")
    display_df = result[display_cols].copy()
    edited_df = st.data_editor(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Caught": st.column_config.CheckboxColumn(
                "Caught", help="Mark Pokémon as caught"
            )
        },
        disabled=[col for col in display_cols if col != "Caught"],
    )
    if not edited_df["Caught"].equals(display_df["Caught"]):
        # Reload the latest caught set to avoid losing updates when multiple
        # reruns are triggered in quick succession by checkbox edits.
        current_set = set(st.session_state.get("caught_set", set()))
        for name, old, new in zip(
            display_df["Name"], display_df["Caught"], edited_df["Caught"]
        ):
            if old == new:
                continue
            if new:
                current_set.add(name)
            else:
                current_set.discard(name)
        save_caught(current_set)
        st.session_state.caught_set = current_set
    csv = edited_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download results",
        data=csv,
        file_name="rarity_results.csv",
        mime="text/csv",
    )
    st.divider()

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
        if selected_name in caught_set:
            if st.button("Unmark as caught"):
                caught_set.remove(selected_name)
                save_caught(caught_set)
                st.session_state.caught_set = caught_set
        else:
            if st.button("Mark as caught"):
                caught_set.add(selected_name)
                save_caught(caught_set)
                st.session_state.caught_set = caught_set

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
