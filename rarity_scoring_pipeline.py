"""Compute adjusted Pokémon rarity scores using encounter frequency and catch difficulty."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

DATA_FILE = Path(__file__).with_name("pokemon_rarity_analysis_enhanced.csv")
OUTPUT_FILE = Path(__file__).with_name("pokemon_rarity_with_final.csv")


def main() -> None:
    df = pd.read_csv(
        DATA_FILE,
        sep=";",
        decimal=",",
        encoding="utf-8",
    )

    required = {
        "Structured_Spawn_Data_Score",
        "Enhanced_Curated_Data_Score",
        "PokemonDB_Catch_Rate_Score",
        "Average_Rarity_Score",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Ensure numeric types and handle missing values
    encounter_cols = ["Structured_Spawn_Data_Score", "Enhanced_Curated_Data_Score"]
    df[encounter_cols] = df[encounter_cols].apply(pd.to_numeric, errors="coerce")
    encounter_rate = df[encounter_cols].mean(axis=1, skipna=True).fillna(0) * 10

    catch_success_rate = pd.to_numeric(
        df["PokemonDB_Catch_Rate_Score"], errors="coerce"
    ).fillna(0) * 10

    adjusted_score = encounter_rate * catch_success_rate

    min_score = adjusted_score.min()
    max_score = adjusted_score.max()
    if max_score == min_score:
        df["rarity_score_final"] = 10
    else:
        df["rarity_score_final"] = 10 * (
            (adjusted_score - min_score) / (max_score - min_score)
        )

    output_cols = [
        "Number",
        "Name",
        "Spawn_Type",
        "Average_Rarity_Score",
        "Recommendation",
        "Data_Sources",
        "Structured_Spawn_Data_Score",
        "Enhanced_Curated_Data_Score",
        "PokemonDB_Catch_Rate_Score",
        "rarity_score_final",
    ]
    df.to_csv(
        OUTPUT_FILE,
        columns=output_cols,
        sep=";",
        index=False,
        float_format="%.2f",
        encoding="utf-8",
    )

    # Diagnostics
    print("Top 10 rarest (old)")
    print(
        df.nsmallest(10, "Average_Rarity_Score")[
            ["Name", "Average_Rarity_Score"]
        ].to_string(index=False)
    )

    print("\nTop 10 most common (old)")
    print(
        df.nlargest(10, "Average_Rarity_Score")[
            ["Name", "Average_Rarity_Score"]
        ].to_string(index=False)
    )

    print("\nTop 10 rarest (new)")
    print(
        df.nsmallest(10, "rarity_score_final")[
            ["Name", "rarity_score_final"]
        ].to_string(index=False)
    )

    print("\nTop 10 most common (new)")
    print(
        df.nlargest(10, "rarity_score_final")[
            ["Name", "rarity_score_final"]
        ].to_string(index=False)
    )

    snorlax = df[df["Name"] == "Snorlax"].iloc[0]
    print(
        f"\nSnorlax old score: {snorlax['Average_Rarity_Score']}, new score: {snorlax['rarity_score_final']:.2f}"
    )

    try:
        import matplotlib.pyplot as plt

        plt.scatter(encounter_rate, catch_success_rate, c=df["rarity_score_final"], cmap="viridis")
        plt.xlabel("Encounter Rate (%)")
        plt.ylabel("Catch Success Rate (%)")
        plt.colorbar(label="Final Rarity Score")
        plt.title("Encounter vs Catch Success")
        plot_file = OUTPUT_FILE.with_suffix("_scatter.png")
        plt.savefig(plot_file, dpi=150, bbox_inches="tight")
        print(f"Scatter plot saved to {plot_file}")
    except Exception as exc:  # pragma: no cover - optional plot
        print(f"Plotting skipped: {exc}")


if __name__ == "__main__":
    main()
