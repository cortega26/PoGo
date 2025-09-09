import json
import logging
import random
import time
import uuid
from typing import Optional, Dict, Any

import requests

logger = logging.getLogger(__name__)


def slugify_name(name: str) -> str:
    """Normalize Pokémon names for use in URLs."""
    slug = name.lower().replace("♀", "-f").replace("♂", "-m")
    slug = slug.replace(":", "").replace("'", "").replace(".", "")
    slug = slug.replace("alolan ", "").replace("galarian ", "")
    return slug.replace("é", "e").replace(" ", "-")


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
