"""Command line interface for pogorarity."""

from typing import Optional
import argparse
from scraper import EnhancedRarityScraper
import logging

logger = logging.getLogger(__name__)


def main(limit: Optional[int] = None) -> None:
    """Run the rarity scraper with an optional PokemonDB limit."""
    scraper = EnhancedRarityScraper()
    scraper.scrape_limit = limit

    try:
        pokemon_data = scraper.aggregate_data()
        scraper.report_data_source_quality()
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
    args = parser.parse_args()
    main(limit=args.limit)
