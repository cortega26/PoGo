from __future__ import annotations

"""Data normalization utilities for encounter records."""

from enum import Enum
from typing import Iterable, List, Tuple

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator


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
        key = record.pokemon_name.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(record)
    return normalized, errors
