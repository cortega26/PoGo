import sys
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
        encoding="utf-8",
    )


def main() -> None:
    try:
        st.markdown(
            "<h1 style='text-align: center; color: white;'>Pokémon Rarity Recommendations</h1>", unsafe_allow_html=True)

        df = load_data()

        st.markdown(
            "<h3 style='color: white;'>Search for a Pokémon by name</h3>", unsafe_allow_html=True)
        name = st.text_input("Pokémon name", placeholder="Enter Pokémon name here",
                             key="pokemon_name")

        if name:
            # Filter names starting with the input string (case-insensitive)
            result = df[df["Name"].str.lower().str.startswith(name.lower())]
            if not result.empty:
                display_cols = [
                    "Recommendation",
                    "Average_Rarity_Score",
                    "Structured_Spawn_Data_Score",
                    "Enhanced_Curated_Data_Score",
                    "PokemonDB_Catch_Rate_Score",
                    "Inferred_Score",
                ]
                st.markdown(
                    "<h3 style='color: white;'>Recommendation and scores</h3>", unsafe_allow_html=True)
                styled_df = result.set_index("Name")[display_cols].style.format({
                    "Average_Rarity_Score": "{:.2f}",
                    "Structured_Spawn_Data_Score": "{:.2f}",
                    "Enhanced_Curated_Data_Score": "{:.2f}",
                    "PokemonDB_Catch_Rate_Score": "{:.2f}",
                    "Inferred_Score": "{:.2f}",
                })
                # Adjust column widths for better UX
                styled_df = styled_df.set_table_styles([
                    {'selector': 'th.col0', 'props': [
                        ('min-width', '150px')]},  # Name column wider
                    # Recommendation column wider
                    {'selector': 'th.col1', 'props': [('min-width', '180px')]},
                    {'selector': 'th', 'props': [
                        ('max-width', '120px'), ('overflow', 'hidden'), ('text-overflow', 'ellipsis')]},
                    {'selector': 'td', 'props': [
                        ('max-width', '120px'), ('overflow', 'hidden'), ('text-overflow', 'ellipsis')]},
                ])
                st.dataframe(styled_df)
            else:
                st.warning("No Pokémon found with that name.")
        else:
            st.info("Enter a Pokémon name to see recommendation and scores.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.write("Please check the console for more details.")


if __name__ == "__main__":
    main()
