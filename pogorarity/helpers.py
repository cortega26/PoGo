import logging
import json
import random
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Set

import pandas as pd
import requests

logger = logging.getLogger(__name__)

FAVORITES_DIR = Path.home() / ".pogorarity"
FAVORITES_FILE = FAVORITES_DIR / "favorites.json"


def load_favorites() -> Set[int]:
    """Load the set of favorited Pokédex numbers from disk."""
    if FAVORITES_FILE.exists():
        try:
            data = json.loads(FAVORITES_FILE.read_text(encoding="utf-8"))
            return {int(n) for n in data}
        except json.JSONDecodeError:
            return set()
    return set()


def save_favorites(favorites: Set[int]) -> None:
    """Persist the set of favorited Pokédex numbers."""
    FAVORITES_DIR.mkdir(parents=True, exist_ok=True)
    FAVORITES_FILE.write_text(
        json.dumps(sorted(favorites)), encoding="utf-8"
    )


def toggle_favorite(number: int) -> Set[int]:
    """Toggle a Pokémon's favorite status and return the updated set."""
    favorites = load_favorites()
    if number in favorites:
        favorites.remove(number)
    else:
        favorites.add(number)
    save_favorites(favorites)
    return favorites


def slugify_name(name: str) -> str:
    """Normalize Pokémon names for use in URLs."""
    slug = name.lower().replace("♀", "-f").replace("♂", "-m")
    slug = slug.replace(":", "").replace("'", "").replace(".", "")
    slug = slug.replace("alolan ", "").replace("galarian ", "")
    return slug.replace("é", "e").replace(" ", "-")


def top_three_summary(df: pd.DataFrame) -> str:
    """Return a short summary of the three rarest Pokémon in ``df``.

    Parameters
    ----------
    df:
        DataFrame containing at least ``Name`` and ``Average_Rarity_Score``
        columns.

    Returns
    -------
    str
        A sentence listing the top three rare Pokémon for sharing.
    """

    top = df.nsmallest(3, "Average_Rarity_Score")["Name"].tolist()
    if not top:
        return "No Pokémon found"
    return f"Rarest Pokémon: {', '.join(top)}"


def safe_request(
    url: str,
    retries: int = 3,
    session: Optional[requests.Session] = None,
    delay: float = 1.0,
    metrics: Optional[Dict[str, Any]] = None,
) -> requests.Response:
    """Make a resilient HTTP GET request with logging and basic metrics."""
    sess = session or requests.Session()
    backoff = delay
    for attempt in range(retries):
        request_id = uuid.uuid4().hex[:8]
        start = time.time()
        try:
            response = sess.get(url, timeout=15)
            latency = time.time() - start
            if metrics is not None:
                metrics.setdefault("latencies", []).append(latency)
                metrics["requests"] = metrics.get("requests", 0) + 1
            log_data = {
                "event": "request",
                "url": url,
                "status": response.status_code,
                "attempt": attempt + 1,
                "latency": round(latency, 2),
                "request_id": request_id,
            }
            logger.info(json.dumps(log_data))
            if response.status_code == 429:
                if metrics is not None:
                    metrics["errors"] = metrics.get("errors", 0) + 1
                wait = backoff + random.uniform(0, delay)
                time.sleep(wait)
                backoff *= 2
                continue
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            latency = time.time() - start
            if metrics is not None:
                metrics.setdefault("latencies", []).append(latency)
                metrics["requests"] = metrics.get("requests", 0) + 1
                metrics["errors"] = metrics.get("errors", 0) + 1
            log_data = {
                "event": "request_error",
                "url": url,
                "attempt": attempt + 1,
                "error": str(e),
                "latency": round(latency, 2),
                "request_id": request_id,
            }
            logger.warning(json.dumps(log_data))
            if attempt == retries - 1:
                raise
            wait = backoff + random.uniform(0, delay)
            time.sleep(wait)
            backoff *= 2
    raise requests.RequestException(f"Failed to fetch {url} after {retries} attempts")
