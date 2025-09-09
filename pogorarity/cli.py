"""Command line interface for pogorarity."""

from typing import Optional
import argparse
import logging

from .scraper import EnhancedRarityScraper

logger = logging.getLogger(__name__)


def main(limit: Optional[int] = None, dry_run: bool = False) -> None:
    """Run the rarity scraper with an optional PokemonDB limit."""
    scraper = EnhancedRarityScraper()
    scraper.scrape_limit = limit

    try:
        pokemon_data = scraper.aggregate_data()
        scraper.report_data_source_quality()
        if not dry_run:
            scraper.export_to_csv(pokemon_data)
        scraper.generate_summary_report(pokemon_data)
        scraper.report_metrics()
        print(
            "\n🎉 Enhanced analysis complete! Check 'pokemon_rarity_analysis_enhanced.csv' for full results."
        )
        print(
            "✨ Key improvements: Fixed categorization bugs, added multiple data sources, enhanced reporting"
        )
    except Exception as e:  # pragma: no cover - logging side effect
        logger.error("Error during execution: %s", e)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pokemon GO rarity analysis")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of Pokemon scraped from PokemonDB for testing",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the scraper without writing CSV output",
    )
    args = parser.parse_args()
    main(limit=args.limit, dry_run=args.dry_run)
