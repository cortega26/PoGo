# PoGo Rarity
>
> Aggregates public Pokémon GO data sources to recommend which monsters to keep or trade.

![tests](https://img.shields.io/badge/tests-passing-brightgreen) ![status](https://img.shields.io/badge/status-experimental-blue)

![Streamlit UI](docs/screenshot.png)

## Overview

PoGo Rarity collects spawn and catch-rate information from multiple community datasets and websites, normalises the values and produces a single CSV with recommendations. A small Streamlit app lets you explore the results interactively.

## Architecture

```mermaid
flowchart LR
  subgraph CLI
    A["pokemon-rarity\nCLI"]
  end
  subgraph Web
    B["Streamlit UI"]
  end
  A --> S[Scraper]
  S -->|HTTP| PokeDB[PokemonDB]
  S -->|HTTP| GOHub[GO Hub]
  S -->|HTTP| Structured[Structured JSON]
  S -->|reads| Curated[(Curated JSON)]
  S -->|writes| CSV[(analysis CSV)]
  B -->|reads| CSV
```

## Scoring Model

The pipeline aggregates rarity information from three sources:

- Structured Spawn Data
- Enhanced Curated Data
- PokemonDB Catch Rate

Each source's raw spawn chance or catch rate is normalised onto a 0–10
scale where 0 denotes the rarest encounters and 10 the most common. The
scores are combined using a weighted average:

- Structured Spawn Data – weight 1.0
- Enhanced Curated Data – weight 1.0
- PokemonDB Catch Rate – weight 2.0

The resulting `Average_Rarity_Score` feeds two threshold sets:

- Rarity bands: `<2` Very Rare, `2–4` Rare, `4–7` Uncommon, `≥7` Common.
- Trading recommendations: score `<4` → "Should Always Trade", `4–7` →
  "Depends on Circumstances", `≥7` → "Safe to Transfer". Legendary,
  event-only, and evolution-only species override these thresholds with
  conservative recommendations.

When no source provides a score, inference rules in
[data/infer_missing_rarity_rules.json](data/infer_missing_rarity_rules.json)
assign default values for specific groups such as pseudo-legendaries or
starters.

## Quickstart

### Prerequisites

- Python ≥3.10
- Node ≥18 (for Markdown linting)
- Optional: Docker for deployment

### Setup

```bash
git clone <repo>
cd <repo>
pip install -e .
```

### Run

```bash
# scrape a small sample without writing a file
pokemon-rarity --limit 5 --dry-run

# quick one-minute demo
pokemon-rarity --limit 1 --dry-run

# launch the Streamlit interface on http://localhost:8501
streamlit run app.py
```

## Configuration

| Name | Type | Default | Required | Description |
|---|---|---|---|---|
| N/A | – | – | – | Configuration is handled via CLI flags (`--limit`, `--dry-run`, `--output-dir`). |

## Commands

```bash
# run tests
python -m pytest

# lint markdown files
npx markdownlint-cli README.md AGENTS.md

# build the package
python -m build
```

## Usage Examples

```bash
$ pokemon-rarity --limit 2 --dry-run
INFO - Aggregating rarity data from multiple enhanced sources...
INFO - Fetching structured spawn data...
INFO - Attempting to scrape Pokemon Database...
```

The scraper emits structured JSON logs per run in `pogorarity/run_log.jsonl` which the Streamlit UI surfaces.

```http
GET / HTTP/1.1
Host: localhost:8501
```

The above HTTP request returns the Streamlit landing page after running `streamlit run app.py`.

## Deployment

- **Docker**: TODO create Dockerfile.
- **Kubernetes**: build an image and expose the Streamlit port 8501; mount output directory for CSVs.
- Run migrations or seeds: not applicable.

## Testing & QA

- Run `python -m pytest` for the unit test suite.
- Tests use fixtures under `tests/fixtures`.
- Coverage: TODO add coverage tooling.

## Observability

- Request logs are written to `pogorarity/pogo_debug.log`.
- Basic metrics (`requests`, `errors`, `latencies`) are available on the `EnhancedRarityScraper.metrics` dict.
- Run metadata with `run_id` is appended to `pogorarity/run_log.jsonl`.
- Health checks: ensure the CSV exists and Streamlit responds on `/` or query `/health`.

## Security & Privacy

- No authentication built in; run behind a trusted network.
- Scraper obeys polite delays and logs all outbound requests.
- Do not store PII; generated CSV contains only public game data.

## Troubleshooting

| Issue | Cause | Fix |
|---|---|---|
| ModuleNotFoundError | Dependencies missing | `pip install -e .` |
| HTTP 429 errors | Rate limiting by external sites | Re-run later; scraper backs off automatically |
| CSV not generated | `--dry-run` used or path unwritable | Remove `--dry-run` or set `--output-dir` |
| Streamlit shows blank table | CSV missing | Run scraper first |
| Tests fail to import requests | Dependencies missing | `pip install -e .` |
| Markdown lint fails | `markdownlint-cli` not installed | `npm install -g markdownlint-cli` |
| Network timeouts | External sites slow | Increase `--limit` slowly or retry |
| Permission denied writing CSV | Output directory protected | Use a writable path |
| Streamlit port in use | Another service on 8501 | `streamlit run app.py --server.port 8502` |
| CLI runs too long | Scraping full Pokédex | Use `--limit` during development |

## Contributing

1. Fork and clone the repo.
2. Create a feature branch from `main`.
3. Run tests and lint before committing.
4. Submit a pull request and mention maintainers.

See [AGENTS.md](AGENTS.md) for automation details.

## License & Support

- License: [MIT](LICENSE)
- Support: open an issue or contact `support@example.com`
