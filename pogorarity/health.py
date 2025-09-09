"""Health check utilities for cache freshness."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from fastapi import FastAPI

DATA_FILE = Path(__file__).resolve().parent.parent / "pokemon_rarity_analysis_enhanced.csv"


def check_cache() -> dict:
    """Return cache freshness info for the rarity CSV."""
    if DATA_FILE.exists():
        mtime = datetime.fromtimestamp(DATA_FILE.stat().st_mtime, tz=timezone.utc)
        fresh = datetime.now(tz=timezone.utc) - mtime < timedelta(days=1)
        return {"cache_fresh": fresh, "last_updated": mtime.isoformat()}
    return {"cache_fresh": False, "last_updated": None}


app = FastAPI()


@app.get("/health")
def health() -> dict:
    """FastAPI endpoint exposing cache status."""
    return check_cache()
