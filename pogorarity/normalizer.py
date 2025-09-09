from __future__ import annotations

"""Data normalization utilities for encounter records.

This module previously only validated basic encounter fields.  The rarity
pipeline however pulls Pokémon names from many heterogeneous sources which may
use inconsistent casing, punctuation or even misspellings.  To ensure all data
joins correctly we now expose helpers to canonicalize Pokémon names and map
them to their National Dex identifiers.
"""

from enum import Enum
from typing import Iterable, List, Tuple
import json
import re
import unicodedata
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

# ---------------------------------------------------------------------------
# Name canonicalisation
# ---------------------------------------------------------------------------

# Common misspellings seen in community sourced data.  Values must be lowercase
# because the canonicalisation routine lowercases prior to lookup.
_MISSPELLINGS = {
    "balbusaur": "bulbasaur",
    "bulbasaor": "bulbasaur",
    "squitle": "squirtle",
    "char mander": "charmander",
    "charmender": "charmander",
}


def _strip_accents(text: str) -> str:
    """Remove accents/diacritics from *text*.

    The project avoids external dependencies, so ``unicodedata`` is used rather
    than ``unidecode``.
    """

    normal = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normal if not unicodedata.combining(ch))


def canonicalize_name(raw: str) -> str:
    """Return a canonical Pokémon name.

    - normalises case and whitespace
    - removes punctuation/diacritics ("Pokémon" → "Pokemon")
    - fixes common misspellings (e.g. ``Balbusaur`` → ``Bulbasaur``)
    - preserves regional form prefixes (Alolan, Galarian, ...)
    """

    if not isinstance(raw, str):  # defensive, helps tests
        raise TypeError("name must be a string")

    text = _strip_accents(raw).lower().strip()
    text = re.sub(r"[._'`]+", "", text)  # remove punctuation
    text = re.sub(r"\s+", " ", text)

    # handle regional forms but keep prefix for display
    region = None
    for prefix in ("alolan", "galarian", "hisuian", "paldean"):
        if text.startswith(prefix + " "):
            region = prefix.capitalize()
            text = text[len(prefix) + 1 :]
            break

    text = _MISSPELLINGS.get(text, text)

    parts = [p.capitalize() for p in text.split()]
    name = " ".join(parts)
    return f"{region} {name}" if region else name


# Build mapping from canonical name to National Dex number for join integrity.
_POKEMON_LIST_PATH = Path(__file__).resolve().parent.parent / "data" / "pokemon_list.json"
with _POKEMON_LIST_PATH.open(encoding="utf-8") as fh:
    _NAME_TO_ID = {
        canonicalize_name(p["name"]): p["number"]
        for p in json.load(fh)
    }


def lookup_number(name: str) -> int | None:
    """Return National Dex number for *name* after canonicalisation."""

    return _NAME_TO_ID.get(canonicalize_name(name))



class Rarity(str, Enum):
    """Canonical rarity categories."""

    common = "common"
    uncommon = "uncommon"
    rare = "rare"
    legendary = "legendary"


class Encounter(BaseModel):
    """Normalized encounter record for a single Pokémon."""

    pokemon_name: str
    rarity: Rarity
    spawn_rate: float | None = None
    source: str | None = None

    model_config = ConfigDict(extra="ignore")

    @field_validator("rarity", mode="before")
    @classmethod
    def _coerce_rarity(cls, value: object) -> str | Rarity:
        """Allow numeric scores or strings to map to ``Rarity``."""
        if isinstance(value, (int, float)):
            score = float(value)
            if score <= 0:
                return Rarity.legendary
            if score < 3:
                return Rarity.rare
            if score < 6:
                return Rarity.uncommon
            return Rarity.common
        if isinstance(value, str):
            v = value.strip().lower().replace(" ", "_")
            if v not in Rarity.__members__ and v not in Rarity._value2member_map_:
                raise ValueError("invalid rarity")
            return v
        raise ValueError("invalid rarity type")

    @field_validator("spawn_rate", mode="before")
    @classmethod
    def _coerce_spawn_rate(cls, value: object) -> float | object:
        if isinstance(value, str):
            v = value.strip()
            if v.endswith("%"):
                return float(v[:-1]) / 100.0
            return float(v)
        return value


def normalize_encounters(rows: Iterable[dict]) -> Tuple[List[Encounter], List[str]]:
    """Validate and de-duplicate raw encounter rows.

    Returns a tuple of ``(normalized_records, error_messages)``.
    """
    normalized: List[Encounter] = []
    errors: List[str] = []
    seen: set[str] = set()
    for row in rows:
        try:
            record = Encounter.model_validate(row)
        except ValidationError as exc:
            errors.append(str(exc))
            continue
        # use canonical name for duplicate detection
        key = canonicalize_name(record.pokemon_name)
        if key in seen:
            continue
        seen.add(key)
        record.pokemon_name = key
        normalized.append(record)
    return normalized, errors
