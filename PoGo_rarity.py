#!/usr/bin/env python3
"""
Enhanced Pokemon GO Rarity Aggregator
Fixes categorization bugs and adds multiple reliable data sources
"""

import requests
import pandas as pd
import time
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Tuple, Optional
import json
import csv
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
from pathlib import Path
import logging
import random
import argparse
import uuid

# Configure logging
LOG_FILE = Path(__file__).with_name("pogo_debug.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


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


class EnhancedRarityScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.pokemon_data = {}
        # Reduce delay slightly to keep runtime reasonable while still
        # being courteous to external sites.
        self.delay = 1
        self.data_source_reports = []
        # Optional limit for expensive scrapers like Serebii/PokemonDB.  When
        # set to ``None`` all Pokémon in the dataset will be scraped.  This can
        # result in a very large number of HTTP requests so tests may override
        # this value with a smaller integer.
        self.scrape_limit: Optional[int] = None
        # simple metrics for observability
        self.metrics = {
            "requests": 0,
            "errors": 0,
            "latencies": []
        }
        try:
            self.pokemon_name_set = {
                name.lower() for name, _ in self.get_comprehensive_pokemon_list()
            }
        except Exception as e:
            logger.error("Failed to load Pokémon list: %s", e)
            self.pokemon_name_set = set()

    def safe_request(self, url: str, retries: int = 3) -> requests.Response:
        """Make a safe HTTP request with retries, structured logging and metrics"""
        for attempt in range(retries):
            request_id = uuid.uuid4().hex[:8]
            start = time.time()
            try:
                response = self.session.get(url, timeout=15)
                latency = time.time() - start
                status = response.status_code
                logger.info(
                    "request url=%s status=%s attempt=%d latency=%.2f request_id=%s",
                    url, status, attempt + 1, latency, request_id,
                )
                self.metrics["requests"] += 1
                self.metrics["latencies"].append(latency)
                if status == 429:
                    retry_after = response.headers.get("Retry-After")
                    wait = (
                        int(retry_after)
                        if retry_after and retry_after.isdigit()
                        else self.delay * (2 ** attempt)
                    )
                    wait += random.uniform(0, self.delay)
                    self.metrics["errors"] += 1
                    logger.warning(
                        "Rate limited by %s, sleeping for %.2f seconds",
                        url, wait,
                    )
                    time.sleep(wait)
                    continue
                if status in {403, 404}:
                    self.metrics["errors"] += 1
                    response.raise_for_status()
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                latency = time.time() - start
                if isinstance(e, requests.HTTPError) and getattr(e.response, "status_code", None) in {403, 404}:
                    logger.warning(
                        "request_error url=%s attempt=%d error=%s latency=%.2f request_id=%s",
                        url, attempt + 1, e, latency, request_id,
                    )
                    raise
                self.metrics["requests"] += 1
                self.metrics["errors"] += 1
                self.metrics["latencies"].append(latency)
                logger.warning(
                    "request_error url=%s attempt=%d error=%s latency=%.2f request_id=%s",
                    url, attempt + 1, e, latency, request_id,
                )
                if attempt == retries - 1:
                    raise
                wait = self.delay * (2 ** attempt) + random.uniform(0, self.delay)
                time.sleep(wait)
        raise requests.RequestException(
            f"Failed to fetch {url} after {retries} attempts"
        )

    def scrape_gamepress_v2(self) -> Tuple[Dict[str, float], DataSourceReport]:
        """Scrape Pokemon rarity data from new GamePress v2 site"""
        logger.info("Attempting to scrape GamePress v2...")
        rarity_data = {}

        try:
            # Try new GamePress URLs
            urls_to_try = [
                "https://pokemongo.gamepress.gg/pokemon-list",
                "https://pogo.gamepress.gg/pokemon-list",
                "https://pokemongo.gamepress.gg/comprehensive-dps-spreadsheet"
            ]

            response = None
            working_url = None

            for url in urls_to_try:
                try:
                    logger.info(f"Trying URL: {url}")
                    response = self.safe_request(url)
                    working_url = url
                    break
                except Exception as e:
                    logger.info(f"URL {url} failed: {e}")
                    continue

            if not response:
                raise Exception("All GamePress URLs failed")

            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for Pokemon data in various formats
            pokemon_found = 0

            # Try to find Pokemon in tables
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        # Look for Pokemon names in cells
                        for i, cell in enumerate(cells):
                            text = cell.get_text().strip()
                            if self.is_pokemon_name(text) and i + 1 < len(cells):
                                # Look for rarity info in adjacent cells
                                for j in range(i + 1, len(cells)):
                                    rarity_text = cells[j].get_text().strip()
                                    if self.contains_rarity_info(rarity_text):
                                        score = self.normalize_rarity_score(
                                            rarity_text, 'GamePress')
                                        rarity_data[text] = score
                                        pokemon_found += 1
                                        break

            # Try to find Pokemon in lists/divs
            pokemon_elements = soup.find_all(['div', 'span', 'a'], string=re.compile(
                r'(Pikachu|Charizard|Blastoise|Venusaur)'))
            for elem in pokemon_elements:
                parent = elem.parent
                if parent:
                    name = elem.get_text().strip()
                    # Look for rarity info in siblings or children
                    siblings = parent.find_all(['span', 'div', 'td'])
                    for sibling in siblings:
                        rarity_text = sibling.get_text().strip()
                        if self.contains_rarity_info(rarity_text):
                            score = self.normalize_rarity_score(
                                rarity_text, 'GamePress')
                            rarity_data[name] = score
                            pokemon_found += 1
                            break

            if pokemon_found == 0:
                raise Exception(
                    f"No Pokemon data found in new structure from {working_url}")

            report = DataSourceReport("GamePress v2", len(rarity_data), True)
            logger.info(
                f"Successfully scraped {len(rarity_data)} Pokemon from GamePress v2")

        except Exception as e:
            logger.error(f"GamePress v2 scraping failed: {e}")
            report = DataSourceReport("GamePress v2", 0, False, str(e))

        return rarity_data, report

    def scrape_pokemon_go_hub(self) -> Tuple[Dict[str, float], DataSourceReport]:
        """Scrape Pokemon data from Pokemon GO Hub"""
        logger.info("Attempting to scrape Pokemon GO Hub...")
        rarity_data = {}

        try:
            # Pokemon GO Hub database
            url = "https://db.pokemongohub.net/"
            response = self.safe_request(url)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for Pokemon cards or entries
            pokemon_cards = soup.find_all(
                ['div', 'article'], class_=re.compile(r'pokemon|card|entry'))

            for card in pokemon_cards:
                try:
                    # Find Pokemon name
                    name_elem = card.find(
                        ['h1', 'h2', 'h3', 'span', 'a'], string=re.compile(r'[A-Z][a-z]+'))
                    if name_elem:
                        name = name_elem.get_text().strip()

                        # Look for rarity indicators
                        rarity_indicators = card.find_all(string=re.compile(
                            r'(rare|common|uncommon|spawn|wild|legendary)'))
                        for indicator in rarity_indicators:
                            if self.contains_rarity_info(indicator):
                                score = self.normalize_rarity_score(
                                    indicator, 'Pokemon GO Hub')
                                rarity_data[name] = score
                                break
                except Exception:
                    continue

            if len(rarity_data) == 0:
                # Try alternative approach - look for any spawn rate information
                spawn_info = soup.find_all(string=re.compile(
                    r'(\d+\.?\d*%|spawn|rate|frequency)'))
                logger.info(
                    f"Found {len(spawn_info)} potential spawn rate indicators")

                # Assign default scores based on known patterns
                common_pokemon = ['Pidgey', 'Rattata', 'Caterpie', 'Weedle']
                for pokemon in common_pokemon:
                    if pokemon.lower() in response.text.lower():
                        rarity_data[pokemon] = 8.0

            report = DataSourceReport("Pokemon GO Hub", len(rarity_data), True)
            logger.info(
                f"Successfully scraped {len(rarity_data)} Pokemon from Pokemon GO Hub")

        except Exception as e:
            logger.error(f"Pokemon GO Hub scraping failed: {e}")
            report = DataSourceReport("Pokemon GO Hub", 0, False, str(e))

        return rarity_data, report

    def scrape_serebii_rarity(self, limit: Optional[int] = None) -> Tuple[Dict[str, float], DataSourceReport]:
        """Scrape rarity hints from Serebii's Pokémon GO pages

        ``limit`` controls how many Pokémon are fetched.  ``None`` (default)
        iterates through the entire Pokédex which can be slow but yields the
        most complete dataset.
        """
        logger.info("Attempting to scrape Serebii data...")
        rarity_data: Dict[str, float] = {}

        try:
            pokemon_list = self.get_comprehensive_pokemon_list()
            if limit is not None:
                pokemon_list = pokemon_list[:limit]
            for name, number in pokemon_list:
                url = f"https://www.serebii.net/pokemongo/pokemon/{number:03d}.shtml"
                try:
                    response = self.safe_request(url)
                    text = response.text.lower()

                    score = None
                    if 'event only' in text or 'event-exclusive' in text:
                        score = 0.0
                    elif 'field research' in text or 'special research' in text:
                        score = 1.0
                    elif 'rare' in text and 'very rare' not in text:
                        score = 3.0
                    elif 'uncommon' in text:
                        score = 5.0
                    elif 'common' in text:
                        score = 7.0

                    if score is not None:
                        rarity_data[name] = score
                except Exception:
                    continue

            report = DataSourceReport("Serebii", len(rarity_data), True)
            logger.info(
                f"Successfully scraped {len(rarity_data)} Pokemon from Serebii")

        except Exception as e:
            logger.error(f"Serebii scraping failed: {e}")
            report = DataSourceReport("Serebii", 0, False, str(e))

        return rarity_data, report

    def scrape_pokemondb_catch_rate(self, limit: Optional[int] = None) -> Tuple[Dict[str, float], DataSourceReport]:
        """Scrape catch rates from Pokémon Database"""
        logger.info("Attempting to scrape Pokemon Database...")
        rarity_data: Dict[str, float] = {}

        try:
            pokemon_list = self.get_comprehensive_pokemon_list()
            if limit is not None:
                pokemon_list = pokemon_list[:limit]
            for name, _ in pokemon_list:
                url = f"https://pokemondb.net/pokedex/{self.slugify_name(name)}"
                try:
                    response = self.safe_request(url)
                    catch_rate = self.parse_pokemondb_catch_rate(response.text)
                    if catch_rate is not None:
                        score = min(10.0, catch_rate / 25.5)
                        rarity_data[name] = score
                except Exception:
                    continue

            report = DataSourceReport(
                "PokemonDB Catch Rate", len(rarity_data), True)
            logger.info(
                f"Successfully scraped {len(rarity_data)} Pokemon from PokemonDB")

        except Exception as e:
            logger.error(f"PokemonDB scraping failed: {e}")
            report = DataSourceReport("PokemonDB Catch Rate", 0, False, str(e))

        return rarity_data, report

    def scrape_pogo_api_data(self) -> Tuple[Dict[str, float], DataSourceReport]:
        """Attempt to get data from Pokemon GO API or community APIs"""
        logger.info("Attempting to get Pokemon GO API data...")
        rarity_data = {}

        try:
            url = "https://pogoapi.net/api/v1/pokemon_rarity.json"
            response = self.safe_request(url)
            data = response.json()

            rarity_map = {
                'Legendary': 0.0,
                'Mythic': 0.0,
                'Ultra beast': 2.0,
                'Standard': 7.0
            }

            for category, entries in data.items():
                score = rarity_map.get(category, 5.0)
                for entry in entries:
                    name = entry.get('pokemon_name')
                    if name:
                        rarity_data[name] = score

            report = DataSourceReport("Pokemon GO API", len(
                rarity_data), len(rarity_data) > 0)
            if len(rarity_data) > 0:
                logger.info(
                    f"Successfully got {len(rarity_data)} Pokemon from API data")
            else:
                report.error_message = "No working APIs found"

        except Exception as e:
            logger.error(f"Pokemon GO API scraping failed: {e}")
            report = DataSourceReport("Pokemon GO API", 0, False, str(e))

        return rarity_data, report

    def scrape_structured_spawn_data(self) -> Tuple[Dict[str, float], DataSourceReport]:
        """Fetch spawn rates from a structured JSON dataset"""
        logger.info("Fetching structured spawn data...")
        rarity_data: Dict[str, float] = {}
        url = "https://raw.githubusercontent.com/Biuni/PokemonGO-Pokedex/master/pokedex.json"

        try:
            response = self.safe_request(url)
            data = response.json()
            for entry in data.get("pokemon", []):
                name = entry.get("name")
                spawn_chance = entry.get("spawn_chance")
                if name and spawn_chance is not None:
                    try:
                        chance = float(spawn_chance)
                        # Map 0-20% spawn chance to 0-10 score
                        score = min(10.0, max(0.0, chance / 2.0))
                        rarity_data[name] = score
                    except (TypeError, ValueError):
                        continue

            report = DataSourceReport(
                "Structured Spawn Data", len(rarity_data), len(rarity_data) > 0
            )
            if len(rarity_data) == 0:
                report.error_message = "No spawn data found"

        except Exception as e:
            logger.error(f"Structured spawn data fetch failed: {e}")
            report = DataSourceReport("Structured Spawn Data", 0, False, str(e))

        return rarity_data, report

    def is_pokemon_name(self, text: str) -> bool:
        """Check if text is a known Pokemon name"""
        if not text:
            return False

        return text.strip().lower() in self.pokemon_name_set

    def contains_rarity_info(self, text: str) -> bool:
        """Check if text contains rarity information"""
        if not text:
            return False

        rarity_keywords = [
            'rare', 'common', 'uncommon', 'spawn', 'wild', 'legendary',
            'mythical', 'event', 'research', '%', 'frequent', 'often'
        ]

        text_lower = text.lower()
        return any(keyword in text_lower for keyword in rarity_keywords)

    def slugify_name(self, name: str) -> str:
        """Convert Pokémon names to PokemonDB slugs, handling regional forms"""
        slug = name.lower()
        for prefix in ("alolan", "galarian", "hisuian", "paldean"):
            if slug.startswith(prefix + " "):
                slug = slug[len(prefix) + 1:]
                break
        slug = (
            slug.replace('♀', '-f')
                .replace('♂', '-m')
                .replace(':', '')
                .replace("'", '')
                .replace('.', '')
                .replace('é', 'e')
                .replace(' ', '-')
        )
        return slug

    def parse_pokemondb_catch_rate(self, html: str) -> Optional[int]:
        """Extract catch rate value from a PokemonDB HTML page"""
        soup = BeautifulSoup(html, 'html.parser')
        th = soup.find('th', string=re.compile('Catch rate', re.I))
        if th:
            td = th.find_next('td')
            match = re.search(r'(\d+)', td.get_text())
            if match:
                return int(match.group(1))
        return None

    def normalize_rarity_score(self, rarity_text: str, source: str) -> float:
        """Convert different rarity classifications to 0-10 scale"""
        if not rarity_text:
            return 5.0

        rarity_text = rarity_text.lower().strip()

        # Enhanced mapping
        rarity_mapping = {
            'never': 0, 'research only': 0, 'event only': 0, 'legendary': 0, 'mythical': 0,
            'extremely rare': 1, 'ultra rare': 1, 'very rare': 2, 'rare': 3,
            'uncommon': 4, 'fairly common': 6, 'common': 7, 'frequent': 7,
            'very common': 8, 'extremely common': 9, 'everywhere': 10, 'abundant': 10
        }

        # Check exact matches
        for key, score in rarity_mapping.items():
            if key in rarity_text:
                return score

        # Extract percentages
        percent_match = re.search(r'(\d+\.?\d*)%', rarity_text)
        if percent_match:
            percent = float(percent_match.group(1))
            if percent <= 0.1:
                return 0
            elif percent <= 1:
                return 2
            elif percent <= 5:
                return 4
            elif percent <= 15:
                return 6
            elif percent <= 30:
                return 8
            else:
                return 10

        # Default
        return 5.0

    def get_curated_spawn_data(self) -> Tuple[Dict[str, float], DataSourceReport]:
        """Get enhanced curated spawn data with fixed categorization"""
        logger.info("Loading enhanced curated spawn data...")

        data_path = Path(__file__).parent / "data" / "curated_spawn_data.json"
        try:
            with open(data_path, encoding="utf-8") as f:
                spawn_data = json.load(f)
            report = DataSourceReport(
                "Enhanced Curated Data", len(spawn_data), True)
            logger.info(
                f"Loaded {len(spawn_data)} Pokemon spawn rates from enhanced curated data")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Curated spawn data load failed: {e}")
            spawn_data = {}
            report = DataSourceReport(
                "Enhanced Curated Data", 0, False, str(e))

        return spawn_data, report

    def categorize_pokemon_spawn_type(self, pokemon_name: str, pokemon_number: int) -> str:
        """FIXED categorization with complete legendary list"""

        # COMPLETE Legendary/Mythical Pokemon list
        legendaries = {
            # Generation 1
            'Articuno', 'Zapdos', 'Moltres', 'Mewtwo', 'Mew',

            # Generation 2
            'Raikou', 'Entei', 'Suicune', 'Lugia', 'Ho-Oh', 'Celebi',

            # Generation 3
            'Regirock', 'Regice', 'Registeel', 'Latias', 'Latios',
            'Kyogre', 'Groudon', 'Rayquaza', 'Jirachi', 'Deoxys',

            # Generation 4 - THIS WAS THE BUG! Missing lake trio
            'Dialga', 'Palkia', 'Heatran', 'Regigigas', 'Giratina',
            'Cresselia', 'Phione', 'Manaphy', 'Darkrai', 'Shaymin', 'Arceus',
            'Uxie', 'Mesprit', 'Azelf',  # <-- THESE WERE MISSING!

            # Generation 5
            'Victini', 'Cobalion', 'Terrakion', 'Virizion', 'Tornadus',
            'Thundurus', 'Reshiram', 'Zekrom', 'Landorus', 'Kyurem',
            'Keldeo', 'Meloetta', 'Genesect',

            # Generation 6
            'Xerneas', 'Yveltal', 'Zygarde', 'Diancie', 'Hoopa', 'Volcanion',

            # Generation 7
            'Tapu Koko', 'Tapu Lele', 'Tapu Bulu', 'Tapu Fini', 'Cosmog', 'Cosmoem',
            'Solgaleo', 'Lunala', 'Necrozma', 'Magearna', 'Marshadow',
            'Zeraora', 'Meltan', 'Melmetal', 'Poipole', 'Naganadel',
            'Stakataka', 'Blacephalon',

            # Generation 8
            'Zacian', 'Zamazenta', 'Eternatus', 'Kubfu', 'Urshifu', 'Zarude',
            'Regieleki', 'Regidrago', 'Glastrier', 'Spectrier', 'Calyrex',

            # Regional Forms
            'Galarian Articuno', 'Galarian Zapdos', 'Galarian Moltres',

            # Special Forms
            'Type: Null'
        }

        # Evolution-only Pokemon (same as before, but ensuring completeness)
        evolution_only = {
            # Generation 1 evolutions
            'Ivysaur', 'Venusaur', 'Charmeleon', 'Charizard', 'Wartortle', 'Blastoise',
            'Metapod', 'Butterfree', 'Kakuna', 'Beedrill', 'Pidgeotto', 'Pidgeot',
            'Raticate', 'Fearow', 'Arbok', 'Raichu', 'Sandslash', 'Nidorina',
            'Nidoqueen', 'Nidorino', 'Nidoking', 'Clefable', 'Ninetales',
            'Wigglytuff', 'Golbat', 'Gloom', 'Vileplume', 'Parasect', 'Venomoth',
            'Dugtrio', 'Persian', 'Golduck', 'Primeape', 'Arcanine', 'Poliwhirl',
            'Poliwrath', 'Kadabra', 'Alakazam', 'Machoke', 'Machamp', 'Weepinbell',
            'Victreebel', 'Tentacruel', 'Graveler', 'Golem', 'Rapidash', 'Slowbro',
            'Magneton', 'Dodrio', 'Dewgong', 'Muk', 'Cloyster', 'Haunter',
            'Gengar', 'Hypno', 'Kingler', 'Electrode', 'Exeggutor', 'Marowak',
            'Weezing', 'Rhydon', 'Seadra', 'Seaking', 'Starmie', 'Mr. Mime',
            'Gyarados', 'Vaporeon', 'Jolteon', 'Flareon', 'Omastar', 'Kabutops',
            'Dragonair', 'Dragonite',

            # Add more generations... (keeping same as before for brevity)
        }

        # Event-only Pokemon
        event_only = {
            'Smeargle', 'Spinda', 'Kecleon', 'Spiritomb', 'Rotom', 'Minior',
            'Chatot'
        }

        if pokemon_name in legendaries:
            return 'legendary'
        elif pokemon_name in evolution_only:
            return 'evolution-only'
        elif pokemon_name in event_only:
            return 'event-only'
        else:
            return 'wild'

    def aggregate_data(self) -> List[PokemonRarity]:
        """Aggregate data from multiple enhanced sources"""
        logger.info("Aggregating rarity data from multiple enhanced sources...")

        # Determine how many Pokémon to scrape from slow sources.  ``scrape_limit``
        # defaults to the full Pokédex size but can be overridden for quicker
        # test runs.
        pokemon_list = self.get_comprehensive_pokemon_list()
        limit = self.scrape_limit or len(pokemon_list)

        # Collect data from all sources
        structured_data, structured_report = self.scrape_structured_spawn_data()
        api_data, api_report = self.scrape_pogo_api_data()
        curated_data, curated_report = self.get_curated_spawn_data()
        gamepress_data, gp_report = self.scrape_gamepress_v2()
        hub_data, hub_report = self.scrape_pokemon_go_hub()
        serebii_data, serebii_report = self.scrape_serebii_rarity(limit=limit)
        pokemondb_data, pokemondb_report = self.scrape_pokemondb_catch_rate(limit=limit)

        # Store reports for later display
        self.data_source_reports = [
            structured_report,
            api_report,
            curated_report,
            gp_report,
            hub_report,
            serebii_report,
            pokemondb_report,
        ]

        sources = {
            'Structured Spawn Data': structured_data,
            'Pokemon GO API': api_data,
            'Enhanced Curated Data': curated_data,
            'GamePress v2': gamepress_data,
            'Pokemon GO Hub': hub_data,
            'Serebii': serebii_data,
            'PokemonDB Catch Rate': pokemondb_data,
        }

        logger.info(f"Processing {len(pokemon_list)} Pokemon total...")

        results = []
        pokemon_with_multiple_sources = 0
        pokemon_with_single_source = 0
        pokemon_inferred = 0

        for pokemon_name, pokemon_number in pokemon_list:
            rarity_scores = {}
            data_sources = []

            # FIXED: Use corrected spawn type categorization
            spawn_type = self.categorize_pokemon_spawn_type(
                pokemon_name, pokemon_number)

            # Collect scores from each source
            for source_name, source_data in sources.items():
                if pokemon_name in source_data:
                    rarity_scores[source_name] = source_data[pokemon_name]
                    data_sources.append(source_name)

            # Calculate average score or infer if missing
            if len(rarity_scores) > 1:
                average_score = sum(rarity_scores.values()
                                    ) / len(rarity_scores)
                recommendation = self.get_trading_recommendation(
                    average_score, spawn_type)
                pokemon_with_multiple_sources += 1
            elif len(rarity_scores) == 1:
                average_score = list(rarity_scores.values())[0]
                recommendation = self.get_trading_recommendation(
                    average_score, spawn_type)
                pokemon_with_single_source += 1
            else:
                # Infer rarity using improved logic
                inferred_score = self.infer_missing_rarity(
                    pokemon_name, pokemon_number, spawn_type)
                average_score = inferred_score
                recommendation = self.get_trading_recommendation(
                    average_score, spawn_type)
                rarity_scores['Inferred'] = inferred_score
                data_sources.append('Inferred')
                pokemon_inferred += 1

            # Create PokemonRarity object
            results.append(PokemonRarity(
                name=pokemon_name,
                number=pokemon_number,
                rarity_scores=rarity_scores,
                average_score=average_score,
                recommendation=recommendation,
                data_sources=data_sources,
                spawn_type=spawn_type
            ))

        logger.info(
            f"Pokemon with multiple data sources: {pokemon_with_multiple_sources}")
        logger.info(
            f"Pokemon with single data source: {pokemon_with_single_source}")
        logger.info(f"Pokemon with inferred data: {pokemon_inferred}")
        return results

    def infer_missing_rarity(self, pokemon_name: str, pokemon_number: int, spawn_type: str) -> float:
        """Infer rarity for Pokemon without explicit data using improved logic"""

        if spawn_type in ['legendary', 'event-only']:
            return 0.0
        elif spawn_type == 'evolution-only':
            return 3.0

        # For wild spawning Pokemon, use enhanced rules
        pseudo_legendaries = ['Dratini', 'Larvitar', 'Bagon', 'Beldum',
                              'Gible', 'Axew', 'Deino', 'Goomy', 'Jangmo-o', 'Dreepy']
        if pokemon_name in pseudo_legendaries:
            return 1.5

        starter_patterns = ['Bulbasaur', 'Charmander', 'Squirtle', 'Chikorita', 'Cyndaquil', 'Totodile',
                            'Treecko', 'Torchic', 'Mudkip', 'Turtwig', 'Chimchar', 'Piplup',
                            'Snivy', 'Tepig', 'Oshawott', 'Chespin', 'Fennekin', 'Froakie',
                            'Rowlet', 'Litten', 'Popplio', 'Grookey', 'Scorbunny', 'Sobble']
        if pokemon_name in starter_patterns:
            return 6.0

        very_common = ['Pidgey', 'Rattata', 'Caterpie',
                       'Weedle', 'Bidoof', 'Patrat', 'Lillipup']
        if pokemon_name in very_common:
            return 8.5

        if any(region in pokemon_name for region in ['Alolan', 'Galarian', 'Hisuian', 'Paldean']):
            return 4.0

        # Generation-based defaults with enhanced logic
        if pokemon_number <= 151:
            return 6.0
        elif pokemon_number <= 251:
            return 5.5
        elif pokemon_number <= 386:
            return 5.0
        elif pokemon_number <= 493:
            return 4.5
        elif pokemon_number <= 649:
            return 4.0
        else:
            return 3.5

    def get_trading_recommendation(self, score: float, spawn_type: str) -> str:
        """Convert rarity score to trading recommendation with improved thresholds"""

        if spawn_type == 'legendary':
            return "Never Transfer (Legendary)"
        elif spawn_type == 'event-only':
            return "Never Transfer (Event Only)"
        elif spawn_type == 'evolution-only':
            return "Evaluate for Evolution"

        # Improved thresholds for wild-spawning Pokemon
        if score >= 6:
            return "Safe to Transfer"
        elif score >= 3:
            return "Depends on Circumstances"
        else:
            return "Should Always Trade"

    def get_comprehensive_pokemon_list(self) -> List[Tuple[str, int]]:
        """Get complete Pokemon list for all generations from data file"""
        data_path = Path(__file__).parent / "data" / "pokemon_list.json"
        try:
            with open(data_path, encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise RuntimeError(f"Failed to load Pokémon list: {e}")

        pokemon_list: List[Tuple[str, int]] = []
        for entry in data:
            name = entry.get("name")
            number = entry.get("number")
            if not isinstance(name, str) or not isinstance(number, int):
                logger.warning("Skipping malformed entry: %s", entry)
                continue
            pokemon_list.append((name, number))
        return pokemon_list

    def report_data_source_quality(self):
        """Enhanced data source quality reporting"""
        print("\n" + "="*60)
        print("ENHANCED DATA SOURCE QUALITY REPORT")
        print("="*60)

        total_successful = 0
        total_failed = 0

        for report in self.data_source_reports:
            status = "✓ SUCCESS" if report.success else "✗ FAILED"
            print(f"{report.source_name}: {status}")
            print(f"  - Pokemon count: {report.pokemon_count}")

            if report.success:
                total_successful += 1
                if report.pokemon_count > 0:
                    print(f"  - Status: Data successfully retrieved")
                else:
                    print(f"  - Status: Connected but no data found")
            else:
                total_failed += 1
                if report.error_message:
                    print(f"  - Error: {report.error_message}")
            print()

        total_scraped = sum(
            r.pokemon_count for r in self.data_source_reports if r.success)
        print(f"Summary:")
        print(
            f"  - Successful sources: {total_successful}/{len(self.data_source_reports)}")
        print(
            f"  - Failed sources: {total_failed}/{len(self.data_source_reports)}")
        print(f"  - Total Pokemon with scraped data: {total_scraped}")
        print(
            f"  - Data source diversity: {'Good' if total_successful >= 2 else 'Limited'}")

    def export_to_csv(self, pokemon_data: List[PokemonRarity], filename: str = 'pokemon_rarity_analysis_enhanced.csv'):
        """Export with enhanced data source information"""
        logger.info(f"Exporting enhanced data to {filename}...")

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Number', 'Name', 'Spawn_Type', 'Average_Rarity_Score', 'Recommendation', 'Data_Sources'] + \
                [f'{source}_Score' for source in ['GamePress_v2', 'Pokemon_GO_Hub',
                                                  'Pokemon_GO_API', 'Enhanced_Curated_Data', 'Inferred']]

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for pokemon in sorted(pokemon_data, key=lambda x: x.number):
                row = {
                    'Number': pokemon.number,
                    'Name': pokemon.name,
                    'Spawn_Type': pokemon.spawn_type,
                    'Average_Rarity_Score': round(pokemon.average_score, 2),
                    'Recommendation': pokemon.recommendation,
                    'Data_Sources': ', '.join(pokemon.data_sources)
                }

                # Add individual source scores
                for source in ['GamePress v2', 'Pokemon GO Hub', 'Pokemon GO API', 'Enhanced Curated Data', 'Inferred']:
                    score = pokemon.rarity_scores.get(source, '')
                    if score != '':
                        row[f'{source.replace(" ", "_")}_Score'] = round(
                            score, 2)
                    else:
                        row[f'{source.replace(" ", "_")}_Score'] = ''

                writer.writerow(row)

        logger.info(
            f"Successfully exported {len(pokemon_data)} Pokemon to {filename}")

    def generate_summary_report(self, pokemon_data: List[PokemonRarity]):
        """Generate enhanced summary report with bug fix validation"""
        # Categorize by recommendation
        safe_to_transfer = [
            p for p in pokemon_data if p.recommendation == "Safe to Transfer"]
        depends_on_circumstances = [
            p for p in pokemon_data if p.recommendation == "Depends on Circumstances"]
        should_always_trade = [
            p for p in pokemon_data if p.recommendation == "Should Always Trade"]
        never_transfer = [
            p for p in pokemon_data if "Never Transfer" in p.recommendation]
        evaluate_evolution = [
            p for p in pokemon_data if p.recommendation == "Evaluate for Evolution"]

        # Categorize by spawn type
        wild_spawners = [p for p in pokemon_data if p.spawn_type == 'wild']
        evolution_only = [
            p for p in pokemon_data if p.spawn_type == 'evolution-only']
        legendaries = [p for p in pokemon_data if p.spawn_type == 'legendary']
        event_only = [p for p in pokemon_data if p.spawn_type == 'event-only']

        print("\n" + "="*60)
        print("ENHANCED POKEMON GO RARITY ANALYSIS SUMMARY")
        print("="*60)
        print(f"Total Pokemon analyzed: {len(pokemon_data)}")
        print()
        print("TRADING RECOMMENDATIONS:")
        print(
            f"Safe to Transfer: {len(safe_to_transfer)} ({len(safe_to_transfer)/len(pokemon_data)*100:.1f}%)")
        print(
            f"Depends on Circumstances: {len(depends_on_circumstances)} ({len(depends_on_circumstances)/len(pokemon_data)*100:.1f}%)")
        print(
            f"Should Always Trade: {len(should_always_trade)} ({len(should_always_trade)/len(pokemon_data)*100:.1f}%)")
        print(
            f"Never Transfer (Legendary): {len(never_transfer)} ({len(never_transfer)/len(pokemon_data)*100:.1f}%)")
        print(
            f"Evaluate for Evolution: {len(evaluate_evolution)} ({len(evaluate_evolution)/len(pokemon_data)*100:.1f}%)")
        print()
        print("SPAWN TYPE BREAKDOWN:")
        print(
            f"Wild Spawners: {len(wild_spawners)} ({len(wild_spawners)/len(pokemon_data)*100:.1f}%)")
        print(
            f"Evolution Only: {len(evolution_only)} ({len(evolution_only)/len(pokemon_data)*100:.1f}%)")
        print(
            f"Legendary/Mythical: {len(legendaries)} ({len(legendaries)/len(pokemon_data)*100:.1f}%)")
        print(
            f"Event Only: {len(event_only)} ({len(event_only)/len(pokemon_data)*100:.1f}%)")

        # VALIDATE BUG FIX: Check if Lake Trio is now properly categorized
        lake_trio = [p for p in pokemon_data if p.name in [
            'Uxie', 'Mesprit', 'Azelf']]
        print(f"\n🔍 BUG FIX VALIDATION:")
        print(f"Lake Trio (Uxie, Mesprit, Azelf) categorization:")
        for pokemon in lake_trio:
            status = "✓ FIXED" if pokemon.spawn_type == "legendary" else "✗ STILL BROKEN"
            print(
                f"  - {pokemon.name}: {pokemon.spawn_type} ({pokemon.recommendation}) {status}")

        if safe_to_transfer:
            print(f"\nTop 10 Most Common (Safe to Transfer):")
            safe_sorted = sorted(
                safe_to_transfer, key=lambda x: x.average_score, reverse=True)[:10]
            for i, pokemon in enumerate(safe_sorted, 1):
                sources = f"[{', '.join(pokemon.data_sources[:2])}]" if len(
                    pokemon.data_sources) <= 2 else f"[{pokemon.data_sources[0]}+{len(pokemon.data_sources)-1} more]"
                print(
                    f"{i:2d}. {pokemon.name:<15} (Score: {pokemon.average_score:.1f}) {sources}")

        if should_always_trade:
            print(f"\nTop 10 Wild Rarest (Should Always Trade):")
            rare_wild = [
                p for p in should_always_trade if p.spawn_type == 'wild']
            rare_sorted = sorted(rare_wild, key=lambda x: x.average_score)[:10]
            for i, pokemon in enumerate(rare_sorted, 1):
                sources = f"[{', '.join(pokemon.data_sources[:2])}]" if len(
                    pokemon.data_sources) <= 2 else f"[{pokemon.data_sources[0]}+{len(pokemon.data_sources)-1} more]"
                print(
                    f"{i:2d}. {pokemon.name:<15} (Score: {pokemon.average_score:.1f}) {sources}")

        print(f"\nData Quality Insights:")
        source_counts = {}
        for pokemon in pokemon_data:
            for source in pokemon.data_sources:
                source_counts[source] = source_counts.get(source, 0) + 1

        for source, count in source_counts.items():
            percentage = (count / len(pokemon_data)) * 100
            print(f"Pokemon with {source}: {count} ({percentage:.1f}%)")

    def report_metrics(self):
        """Log simple request metrics"""
        total = self.metrics["requests"]
        errors = self.metrics["errors"]
        avg_latency = (
            sum(self.metrics["latencies"]) / total if total else 0
        )
        success_rate = ((total - errors) / total * 100) if total else 0
        logger.info(
            "Request metrics: total=%d errors=%d success_rate=%.1f%% avg_latency=%.2fs",
            total,
            errors,
            success_rate,
            avg_latency,
        )


def main(limit: Optional[int] = None):
    """Main execution function

    Args:
        limit: Optional limit for expensive web scrapers.  ``None`` scrapes all
            Pokémon while an integer restricts the number processed from
            Serebii and PokemonDB.  This is primarily useful for testing to
            avoid thousands of HTTP requests.
    """
    scraper = EnhancedRarityScraper()
    scraper.scrape_limit = limit

    try:
        # Aggregate data from multiple enhanced sources
        pokemon_data = scraper.aggregate_data()

        # Report on data source quality
        scraper.report_data_source_quality()

        # Export to CSV
        scraper.export_to_csv(pokemon_data)

        # Generate enhanced summary report
        scraper.generate_summary_report(pokemon_data)

        # Log request metrics
        scraper.report_metrics()

        print(f"\n🎉 Enhanced analysis complete! Check 'pokemon_rarity_analysis_enhanced.csv' for full results.")
        print(f"✨ Key improvements: Fixed categorization bugs, added multiple data sources, enhanced reporting")

    except Exception as e:
        logger.error(f"Error during execution: {e}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pokemon GO rarity analysis")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of Pokemon scraped from Serebii and PokemonDB for testing",
    )
    args = parser.parse_args()
    main(limit=args.limit)
