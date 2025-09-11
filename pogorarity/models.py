from typing import Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel, Field


class PokemonRarity(BaseModel):
    """Validated representation of aggregated rarity data for a Pokémon."""

    name: str
    number: int
    rarity_scores: Dict[str, float]
    average_score: float
    weighted_average: float
    confidence: float
    recommendation: str
    data_sources: List[str]
    spawn_type: str
    types: List[str] = Field(default_factory=list)
    regions: List[str] = Field(default_factory=list)


class DataSourceReport(BaseModel):
    """Information about the success of scraping a particular data source."""

    source_name: str
    pokemon_count: int
    success: bool
    error_message: Optional[str] = None


class RarityRecord(BaseModel):
    """Normalized rarity information for a single Pokémon from one source."""

    pokemon_name: str
    rarity: float
    source: str
    confidence: float
    timestamp: datetime

