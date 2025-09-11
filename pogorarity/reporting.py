import logging
import os
from typing import Dict, List, Optional

import pandas as pd

from .models import DataSourceReport, PokemonRarity

logger = logging.getLogger(__name__)


def report_metrics(metrics: Dict[str, float]) -> None:
    total = metrics.get("requests", 0)
    errors = metrics.get("errors", 0)
    avg_latency = (
        sum(metrics.get("latencies", [])) / total if total else 0
    )
    success_rate = 100.0 * (1 - errors / total) if total else 0
    logger.info(
        "Request metrics: total=%d errors=%d success_rate=%.1f%% avg_latency=%.2fs",
        total,
        errors,
        success_rate,
        avg_latency,
    )


def report_data_source_quality(reports: List[DataSourceReport]) -> None:
    print("\n" + "=" * 60)
    print("ENHANCED DATA SOURCE QUALITY REPORT")
    print("=" * 60)
    total_successful = 0
    total_failed = 0
    for report in reports:
        status = "✓ SUCCESS" if report.success else "✗ FAILED"
        print(f"{report.source_name}: {status}")
        print(f"  - Pokemon count: {report.pokemon_count}")
        if report.success:
            total_successful += 1
            if report.pokemon_count == 0:
                print("  - Status: Connected but no data found")
        else:
            total_failed += 1
            if report.error_message:
                print(f"  - Error: {report.error_message}")
        print()
    print("Summary:")
    print(f"  - Successful sources: {total_successful}/{len(reports)}")
    print(f"  - Failed sources: {total_failed}/{len(reports)}")
    total_scraped = sum(r.pokemon_count for r in reports if r.success)
    print(f"  - Total Pokemon with scraped data: {total_scraped}")


def export_to_csv(
    pokemon_data: List[PokemonRarity],
    filename: str = "pokemon_rarity_analysis_enhanced.csv",
    output_dir: Optional[str] = None,
) -> None:
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.join(output_dir, filename)
    logger.info("Exporting enhanced data to %s...", filename)
    sources = [
        "Structured Spawn Data",
        "Enhanced Curated Data",
        "PokemonDB Catch Rate",
        "PokeAPI Capture Rate",
    ]
    rows = []
    for pokemon in sorted(pokemon_data, key=lambda x: x.number):
        row = {
            "Number": pokemon.number,
            "Name": pokemon.name,
            "Spawn_Type": pokemon.spawn_type,
            "Average_Rarity_Score": round(pokemon.average_score, 2),
            "Weighted_Average_Rarity_Score": round(pokemon.weighted_average, 2),
            "Confidence": round(pokemon.confidence, 2),
            "Recommendation": pokemon.recommendation,
            "Data_Sources": ", ".join(pokemon.data_sources),
            "Type": ", ".join(pokemon.types) if pokemon.types else None,
            "Region": ", ".join(pokemon.regions) if pokemon.regions else None,
        }
        for source in sources:
            score = pokemon.rarity_scores.get(source)
            col_name = f"{source.replace(' ', '_')}_Score"
            row[col_name] = round(score, 2) if score is not None else None
        rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(
        filename,
        index=False,
        sep=";",
        float_format="%.2f",
        decimal=",",
        encoding="utf-8",
    )
    logger.info("Successfully exported %d Pokemon to %s", len(pokemon_data), filename)


def generate_summary_report(pokemon_data: List[PokemonRarity]) -> str:
    """Return a simple text summary of the aggregated rarity data."""
    lines = ["SUMMARY REPORT"]
    for p in pokemon_data:
        lines.append(
            f"{p.number:03d} {p.name}: {p.average_score:.2f} - {p.recommendation}"
        )
    summary = "\n".join(lines)
    print("\n" + summary)
    return summary
