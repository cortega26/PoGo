from pathlib import Path
import csv
import json
import time
from datetime import datetime
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from .helpers import slugify_name
from .models import RarityRecord

RATE_LIMIT = 1.0
RETRIES = 3


def fetch_with_cache(url: str, cache_file: Path, session: Optional[requests.Session] = None) -> str:
    """Fetch a URL respecting ETag/Last-Modified and local cache."""
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    meta_file = cache_file.with_suffix(cache_file.suffix + ".meta")
    headers = {}
    if meta_file.exists():
        try:
            meta = json.loads(meta_file.read_text())
            if meta.get("etag"):
                headers["If-None-Match"] = meta["etag"]
            if meta.get("last_modified"):
                headers["If-Modified-Since"] = meta["last_modified"]
        except Exception:
            pass
    sess = session or requests.Session()
    for attempt in range(RETRIES):
        time.sleep(RATE_LIMIT)
        resp = sess.get(url, headers=headers)
        if resp.status_code == 304 and cache_file.exists():
            return cache_file.read_text()
        try:
            resp.raise_for_status()
        except requests.RequestException:
            if attempt == RETRIES - 1:
                raise
            time.sleep(RATE_LIMIT * (2 ** attempt))
            continue
        cache_file.write_text(resp.text)
        meta = {
            "etag": resp.headers.get("ETag"),
            "last_modified": resp.headers.get("Last-Modified"),
        }
        meta_file.write_text(json.dumps(meta))
        return resp.text
    raise RuntimeError("unreachable")


def save_records(records: List[RarityRecord], base_path: Path) -> None:
    """Save records to JSON and CSV files."""
    base_path.parent.mkdir(parents=True, exist_ok=True)
    json_path = base_path.with_suffix(".json")
    csv_path = base_path.with_suffix(".csv")
    data = [r.dict() for r in records]
    json_path.write_text(json.dumps(data, default=str))
    if data:
        with csv_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(data[0].keys()))
            writer.writeheader()
            writer.writerows(data)
    else:
        csv_path.write_text("")


RARITY_MAP = {
    "common": 8.0,
    "uncommon": 5.0,
    "rare": 2.0,
    "legendary": 0.5,
}


def parse_go_hub(html: str, timestamp: Optional[datetime] = None) -> List[RarityRecord]:
    """Parse simplified Pokemon GO Hub HTML into RarityRecord objects."""
    soup = BeautifulSoup(html, "html.parser")
    records: List[RarityRecord] = []
    ts = timestamp or datetime.utcnow()
    for row in soup.select("tr"):
        cells = [c.get_text(strip=True) for c in row.find_all("td")]
        if len(cells) >= 2:
            name, rarity_text = cells[0], cells[1].lower()
            score = RARITY_MAP.get(rarity_text, 5.0)
            records.append(
                RarityRecord(
                    pokemon_name=name,
                    rarity=score,
                    source="Pokemon GO Hub",
                    confidence=0.6,
                    timestamp=ts,
                )
            )
    return records


def parse_structured_spawn_data(text: str, timestamp: Optional[datetime] = None) -> List[RarityRecord]:
    data = json.loads(text)
    records: List[RarityRecord] = []
    ts = timestamp or datetime.utcnow()
    for entry in data.get("pokemon", []):
        name = entry.get("name")
        spawn = entry.get("spawn_chance")
        if name and spawn is not None:
            rarity = min(10.0, max(0.0, float(spawn) / 2.0))
            records.append(
                RarityRecord(
                    pokemon_name=name,
                    rarity=rarity,
                    source="Structured Spawn Data",
                    confidence=0.8,
                    timestamp=ts,
                )
            )
    return records


def parse_pokemondb_page(name: str, html: str, timestamp: Optional[datetime] = None) -> Optional[RarityRecord]:
    soup = BeautifulSoup(html, "html.parser")
    th = soup.find("th", string=lambda s: s and "Catch rate" in s)
    if not th:
        return None
    td = th.find_next("td")
    if not td:
        return None
    digits = ''.join(ch for ch in td.get_text() if ch.isdigit())
    if not digits:
        return None
    catch_rate = int(digits)
    rarity = min(10.0, catch_rate / 25.5)
    return RarityRecord(
        pokemon_name=name,
        rarity=rarity,
        source="PokemonDB Catch Rate",
        confidence=0.9,
        timestamp=timestamp or datetime.utcnow(),
    )


def get_structured_spawn_records(cache_dir: str = "data") -> List[RarityRecord]:
    url = "https://raw.githubusercontent.com/Biuni/PokemonGO-Pokedex/master/pokedex.json"
    cache_file = Path(cache_dir) / "structured_spawn_raw.json"
    text = fetch_with_cache(url, cache_file)
    records = parse_structured_spawn_data(text)
    save_records(records, Path(cache_dir) / "structured_spawn_records")
    return records


def get_go_hub_records(cache_dir: str = "data") -> List[RarityRecord]:
    url = "https://db.pokemongohub.net/"
    cache_file = Path(cache_dir) / "go_hub_raw.html"
    html = fetch_with_cache(url, cache_file)
    records = parse_go_hub(html)
    save_records(records, Path(cache_dir) / "go_hub_records")
    return records


def get_pokemondb_records(names: List[str], cache_dir: str = "data") -> List[RarityRecord]:
    records: List[RarityRecord] = []
    session = requests.Session()
    for name in names:
        slug = slugify_name(name)
        url = f"https://pokemondb.net/pokedex/{slug}"
        cache_file = Path(cache_dir) / f"pokemondb_{slug}.html"
        html = fetch_with_cache(url, cache_file, session=session)
        rec = parse_pokemondb_page(name, html)
        if rec:
            records.append(rec)
    save_records(records, Path(cache_dir) / "pokemondb_records")
    return records
