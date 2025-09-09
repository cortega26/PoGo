from typing import Dict, List, Optional

from pydantic import BaseModel


class PokemonRarity(BaseModel):
    """Validated representation of aggregated rarity data for a Pokémon."""

    name: str
    number: int
    rarity_scores: Dict[str, float]
    average_score: float
    recommendation: str
    data_sources: List[str]
    spawn_type: str


class DataSourceReport(BaseModel):
    """Information about the success of scraping a particular data source."""

    source_name: str
    pokemon_count: int
    success: bool
    error_message: Optional[str] = None

