from pathlib import Path

import pandas as pd
import streamlit as st

DATA_FILE = Path(__file__).with_name("pokemon_rarity_analysis_enhanced.csv")

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
    return pd.read_csv(
        DATA_FILE,
        sep=";",
        decimal=",",
        usecols=cols,
    )

def main() -> None:
    st.title("Pokémon Rarity Recommendations")

    df = load_data()

    name = st.text_input("Pokémon name")
    if name:
        result = df[df["Name"].str.contains(name, case=False, na=False)]
        if not result.empty:
            display_cols = [
                "Recommendation",
                "Average_Rarity_Score",
                "Structured_Spawn_Data_Score",
                "Enhanced_Curated_Data_Score",
                "PokemonDB_Catch_Rate_Score",
                "Inferred_Score",
            ]
            st.subheader("Recommendation and scores")
            st.table(result.set_index("Name")[display_cols])
        else:
            st.warning("No Pokémon found with that name.")
    else:
        st.info("Enter a Pokémon name to see recommendation and scores.")

if __name__ == "__main__":
    main()
