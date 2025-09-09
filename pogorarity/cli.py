"""Command line interface for pogorarity."""

from __future__ import annotations

from typing import Optional
import argparse
import json
import logging
from pathlib import Path
from datetime import datetime
import uuid

import pandas as pd

try:  # pragma: no cover - runtime import
    from .normalizer import normalize_encounters
    from .scraper import EnhancedRarityScraper
except ImportError:  # pragma: no cover
    from normalizer import normalize_encounters
    from scraper import EnhancedRarityScraper

logger = logging.getLogger(__name__)
RUN_LOG = Path(__file__).with_name("run_log.jsonl")


def _log_run(entry: dict) -> None:
    with RUN_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")


def _run(
    limit: Optional[int] = None,
    dry_run: bool = False,
    output_dir: Optional[str] = None,
    validate_only: bool = False,
) -> None:
    run_id = uuid.uuid4().hex
    _log_run(
        {
            "run_id": run_id,
            "status": "started",
            "start_time": datetime.utcnow().isoformat(),
            "dry_run": dry_run,
        }
    )

    scraper = EnhancedRarityScraper()
    scraper.scrape_limit = limit
    scraper.output_dir = output_dir

    if validate_only:
        raw_rows = [
            {"pokemon_name": f"Test{i}", "rarity": 5.0} for i in range(limit or 1)
        ]
        _, errors = normalize_encounters(raw_rows)
        print(f"{len(errors)} schema errors.")
        _log_run(
            {
                "run_id": run_id,
                "status": "success",
                "rows": len(raw_rows),
                "end_time": datetime.utcnow().isoformat(),
            }
        )
        return

    try:
        pokemon_data = scraper.aggregate_data()
        scraper.report_data_source_quality()
        rows = len(pokemon_data)

        raw_rows = [
            {"pokemon_name": p.name, "rarity": p.average_score}
            for p in pokemon_data
        ]
        normalized, errors = normalize_encounters(raw_rows)
        if errors:
            print(f"{len(errors)} schema errors.")

        if not dry_run:
            df = pd.DataFrame([r.model_dump() for r in normalized])
            filename = "pokemon_rarity_analysis_enhanced.csv"
            if output_dir:
                Path(output_dir).mkdir(parents=True, exist_ok=True)
                path = Path(output_dir) / filename
            else:
                path = Path(filename)
            df.to_csv(path, index=False)

        scraper.generate_summary_report(pokemon_data)
        scraper.report_metrics()
        _log_run(
            {
                "run_id": run_id,
                "status": "success",
                "rows": rows,
                "end_time": datetime.utcnow().isoformat(),
            }
        )
        print(
            "\n🎉 Enhanced analysis complete! Check 'pokemon_rarity_analysis_enhanced.csv' for full results.",
        )
        print(
            "✨ Key improvements: Fixed categorization bugs, added multiple data sources, enhanced reporting",
        )
    except Exception as e:  # pragma: no cover - logging side effect
        _log_run(
            {
                "run_id": run_id,
                "status": "error",
                "error": str(e),
                "end_time": datetime.utcnow().isoformat(),
            }
        )
        logger.error("Error during execution: %s", e)
        raise


def main(argv: Optional[list[str]] = None) -> None:  # pragma: no cover - thin wrapper
    parser = argparse.ArgumentParser(description="Pokemon GO rarity analysis")
    parser.add_argument(
        "--limit", type=int, default=None, help="Limit number of Pokemon scraped from PokemonDB for testing"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Run the scraper without writing CSV output"
    )
    parser.add_argument(
        "--output-dir", type=str, default=None, help="Directory to save the CSV output file"
    )
    parser.add_argument(
        "--validate-only", action="store_true", help="Validate data without writing CSV output"
    )
    args = parser.parse_args(argv)
    _run(
        limit=args.limit,
        dry_run=args.dry_run,
        output_dir=args.output_dir,
        validate_only=args.validate_only,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
