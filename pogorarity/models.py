from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class PokemonRarity:
    name: str
    number: int
    rarity_scores: Dict[str, float]
    average_score: float
    recommendation: str
    data_sources: List[str]
    spawn_type: str


@dataclass
class DataSourceReport:
    source_name: str
    pokemon_count: int
    success: bool
    error_message: Optional[str] = None

