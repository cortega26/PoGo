"""Command line interface for pogorarity."""

from typing import Optional
import argparse
import json
import logging
from pathlib import Path
from datetime import datetime
import uuid

try:
    # Try relative import (when run as module)
    from .scraper import EnhancedRarityScraper
except ImportError:
    # Fall back to absolute import (when run directly)
    from scraper import EnhancedRarityScraper

logger = logging.getLogger(__name__)
RUN_LOG = Path(__file__).with_name("run_log.jsonl")


def _log_run(entry: dict) -> None:
    """Append a JSON log entry with run metadata."""
    with RUN_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def main(limit: Optional[int] = None, dry_run: bool = False, output_dir: Optional[str] = None) -> None:
    """Run the rarity scraper with an optional PokemonDB limit."""
    run_id = uuid.uuid4().hex
    _log_run({
        "run_id": run_id,
        "status": "started",
        "start_time": datetime.utcnow().isoformat(),
        "dry_run": dry_run,
    })

    scraper = EnhancedRarityScraper()
    scraper.scrape_limit = limit
    scraper.output_dir = output_dir

    try:
        pokemon_data = scraper.aggregate_data()
        scraper.report_data_source_quality()
        rows = len(pokemon_data)
        if not dry_run:
            scraper.export_to_csv(pokemon_data)
        scraper.generate_summary_report(pokemon_data)
        scraper.report_metrics()
        _log_run({
            "run_id": run_id,
            "status": "success",
            "rows": rows,
            "end_time": datetime.utcnow().isoformat(),
        })
        print(
            "\n🎉 Enhanced analysis complete! Check 'pokemon_rarity_analysis_enhanced.csv' for full results.",
        )
        print(
            "✨ Key improvements: Fixed categorization bugs, added multiple data sources, enhanced reporting",
        )
    except Exception as e:  # pragma: no cover - logging side effect
        _log_run({
            "run_id": run_id,
            "status": "error",
            "error": str(e),
            "end_time": datetime.utcnow().isoformat(),
        })
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
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory to save the CSV output file",
    )
    args = parser.parse_args()
    main(limit=args.limit, dry_run=args.dry_run, output_dir=args.output_dir)
